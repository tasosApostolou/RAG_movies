from decimal import Decimal
import json
import os
from pathlib import Path
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, TypedDict
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlmodel import Session
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage,SystemMessage
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
import logging
from langgraph.graph import StateGraph, START, END


from app.core.cost_tracker import _calculate_cost, _empty_usage, _get_usage_from_response
from app.rag.retrieve import search_movies
from app.rag.structured_outputs import MovieFiltersOutput, RetrievalDecisionOutput, SemanticRewriteOutput
# from app.rag.tools import update_semantic_query_tool
from app.rag.vectorstore import vectorstore
from app.rag.memory_service import _append_and_trim_memory, _save_memory_to_session, _save_search_history, _load_memory_from_session
from app.models.conversation import SearchSession, SearchHistory
from app.rag.prompts import ANSWER_SYSTEM_PROMPT, DIRECT_CHAT_SYSTEM_PROMPT, FILTER_SYSTEM_PROMPT, RETRIEVAL_ROUTER_SYSTEM_PROMPT, REWRITE_SYSTEM_PROMPT

import logging

logger = logging.getLogger(__name__)

print("Loading LLM and Chroma vectorstore...")

# ============================================================
# Config
# ============================================================


# # ROOT_DIR = Path(__file__).resolve().parent.parent
# ROOT_DIR = Path(__file__).resolve().parents[2]
# ENV_PATH = ROOT_DIR / ".env"
# load_dotenv(ENV_PATH)

# if not os.environ.get("OPENAI_API_KEY"):
#     import getpass
#     os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API key: ")
    
# CHROMA_DIR = ROOT_DIR / "app" / "chroma_test_db"    

DEFAULT_TOP_K = 15
SUMMARY_K = 5
MAX_MEMORY_MESSAGES = 20


# ============================================================
# LLM / Vectorstore
# ============================================================

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)

print("Loading Chroma vectorstore...")


# ============================================================
# Helpers
# ============================================================

def normalize_key(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _message_content_to_text(content: Any) -> str:
    """
    Keeps DB memory clean even if the model returns structured content blocks.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)

        return "\n".join(parts).strip()

    return str(content)


def _convert_to_lc_messages(
    messages: list[dict[str, str]],
    max_messages: int = 10,
) -> list[BaseMessage]:
    """
    Converts stored DB memory into LangChain chat messages.

    keep only the last max_messages to avoid sending too much context
    into every graph node.
    """
    lc_messages: list[BaseMessage] = []

    for msg in messages[-max_messages:]:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    return lc_messages

MODEL_NAME = "gpt-4.1-mini"


def _update_usage_state_format(
    state: "MovieRAGState",
    response: Any,
    model: str = MODEL_NAME,
) -> dict:
    usage = _get_usage_from_response(response)

    old_usage = state.get("usage", _empty_usage())
    old_cost = state.get("cost", 0.0)

    request_cost = _calculate_cost(
        model=model,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
    )

    return {
        "usage": {
            "input_tokens": old_usage["input_tokens"] + usage["input_tokens"],
            "output_tokens": old_usage["output_tokens"] + usage["output_tokens"],
            "total_tokens": old_usage["total_tokens"] + usage["total_tokens"],
        },
        "cost": old_cost + request_cost,
    }

# ============================================================
# Graph State
# ============================================================

class MovieRAGState(TypedDict):
    user_query: str
    chat_history: list[dict[str, str]]

    semantic_query: str
    rewrite_reasoning: str

    genres: list[str]
    excluded_genres: list[str]
    director: Optional[str]
    year: Optional[int]
    needs_filter: bool
    filter_reasoning: str

    retrieved_movies: list[dict]
    final_answer: str

    needs_retrieval: bool
    routing_reasoning: str

    usage: dict[str, int] # {input_tokens:int, output_tokens:int, total_tokens:int}
    cost: float



retrieval_router_llm = llm.with_structured_output(
    RetrievalDecisionOutput,
    include_raw=True,
)


async def node_decide_retrieval(state: MovieRAGState) -> MovieRAGState:
    lc_history = _convert_to_lc_messages(
        state["chat_history"],
        max_messages=10,
    )

    messages = [
        SystemMessage(content=RETRIEVAL_ROUTER_SYSTEM_PROMPT),
        *lc_history,
        HumanMessage(
            content=f"""
<latest_user_message>
{state["user_query"]}
</latest_user_message>

Decide if this needs a new semantic movie search.
"""
        ),
    ]

    result = await retrieval_router_llm.ainvoke(messages)

    parsed: RetrievalDecisionOutput = result["parsed"]
    raw_message = result["raw"]

    if result.get("parsing_error"):
        raise ValueError(f"Retrieval router parsing failed: {result['parsing_error']}")

    usage_update = _update_usage_state_format(state, raw_message)

    return {
        **state,
        "needs_retrieval": parsed.needs_retrieval,
        "routing_reasoning": parsed.reasoning,
        **usage_update,
    }

def route_after_decision(state: MovieRAGState) -> str:
    if state["needs_retrieval"]:
        return "needs_retrieval"

    return "no_retrieval_needed"

async def node_generate_direct_answer(state: MovieRAGState) -> MovieRAGState:
    lc_history = _convert_to_lc_messages(
        state["chat_history"],
        max_messages=10,
    )

    messages = [
        SystemMessage(content=DIRECT_CHAT_SYSTEM_PROMPT),
        *lc_history,
        HumanMessage(content=state["user_query"]),
    ]

    response = await llm.ainvoke(messages)

    reply_text = _message_content_to_text(response.content)
    usage_update = _update_usage_state_format(state, response)

    return {
        **state,
        "final_answer": reply_text,
        **usage_update,
    }    

 
# ============================================================
# Rewrite query -
# ============================================================

rewrite_llm_structured = llm.with_structured_output(
    SemanticRewriteOutput,
    include_raw=True,
)


async def node_rewrite_query(state: MovieRAGState) -> MovieRAGState:
    lc_history = _convert_to_lc_messages(
        state["chat_history"],
        max_messages=10,
    )

    messages = [
        SystemMessage(content=REWRITE_SYSTEM_PROMPT),
        *lc_history,
        HumanMessage(
            content=f"""
<latest_user_message>
{state["user_query"]}
</latest_user_message>

Rewrite the latest user message into a standalone semantic movie search query.
"""
        ),
    ]

    ai_Message = await rewrite_llm_structured.ainvoke(messages)

    parsed: SemanticRewriteOutput = ai_Message["parsed"]
    raw_message = ai_Message["raw"]

    if ai_Message.get("parsing_error"):
        raise ValueError(f"Rewrite structured output parsing failed: {ai_Message['parsing_error']}")

    usage_update = _update_usage_state_format(state, raw_message)

    return {
        **state,
        "semantic_query": parsed.semantic_query,
        "rewrite_reasoning": parsed.reasoning,
        **usage_update,
    }


# ============================================================
# Filter Extraction
# ============================================================

class UpdateMovieFiltersInput(BaseModel):
    genres: list[str] = Field(default_factory=list)
    excluded_genres: list[str] = Field(default_factory=list)
    director: Optional[str] = None
    year: Optional[int] = None
    needs_filter: bool
    reasoning: str

filter_llm_structured = llm.with_structured_output(
    MovieFiltersOutput,
    include_raw=True,
)

async def node_extract_filters(state: MovieRAGState) -> MovieRAGState:
    lc_history = _convert_to_lc_messages(
        state["chat_history"],
        max_messages=10,
    )

    messages = [
        SystemMessage(content=FILTER_SYSTEM_PROMPT),
        *lc_history,
        HumanMessage(
            content=f"""
<latest_user_message>
{state["user_query"]}
</latest_user_message>

<semantic_query>
{state["semantic_query"]}
</semantic_query>

Extract explicit metadata filters for the latest user request.
"""
        ),
    ]

    result = await filter_llm_structured.ainvoke(messages)

    filters: MovieFiltersOutput = result["parsed"]
    raw_message = result["raw"]

    if result.get("parsing_error"):
        raise ValueError(f"Filter structured output parsing failed: {result['parsing_error']}")

    usage_update = _update_usage_state_format(state, raw_message)

    return {
        **state,
        "genres": filters.genres,
        "excluded_genres": filters.excluded_genres,
        "director": filters.director,
        "year": filters.year,
        "needs_filter": filters.needs_filter,
        "filter_reasoning": filters.reasoning,
        **usage_update,
    }


# ============================================================
# Retrieval
# ============================================================

async def node_retrieve_movies(state: MovieRAGState) -> MovieRAGState:

    # logger.info(
    #     "Retrieval input | semantic_query=%r | genres=%s | excluded_genres=%s | director=%s | year=%s | k=%s"
    #     state["semantic_query"],
    #     state["genres"],
    #     state["excluded_genres"],
    #     state["director"],
    #     state["year"],
    #     DEFAULT_TOP_K
    # )
    logger.info(f"Retrieval input | semantic_query={state["semantic_query"]} | genres={state["genres"]} | excluded_genres={state["excluded_genres"]} | director={state["director"]} | year={state["year"]} | k={DEFAULT_TOP_K}")

    
    retrieved_movies = await search_movies(
        semantic_query=state["semantic_query"],
        genres=state["genres"],
        excluded_genres=state["excluded_genres"],
        director=state["director"],
        year=state["year"],
        default_k=DEFAULT_TOP_K,
        summary_k = SUMMARY_K,
    )

    for i, movie in enumerate(retrieved_movies, start=1):
        logger.info(
            "Retrieved #%s | movie_id=%s | title=%s | year=%s | genres=%s | director=%s | response =%s",
            i,
            movie.get("movie_id"),
            movie.get("title"),
            movie.get("year"),
            movie.get("genres"),
            movie.get("director"),
            movie.get("plot")[:700]
            # movie.get
            # movie.get("is_synthetic_query","")
        )

    return {
        **state,
        "retrieved_movies": retrieved_movies,
    }



def format_movies_for_context(movies: list[dict]) -> str:
    if not movies:
        return "No movies retrieved."

    blocks = []

    for i, movie in enumerate(movies, start=1):
        block = f"""
<movie index="{i}">
<title>{movie.get("title")}</title>
<year>{movie.get("year")}</year>
<genres>{movie.get("genres")}</genres>
<director>{movie.get("director")}</director>

<plot or synthetic query>
{movie.get("plot")}
</plot or synthetic query>
</movie>
"""
        blocks.append(block.strip())

    return "\n\n".join(blocks)

async def node_generate_answer(state: MovieRAGState) -> MovieRAGState:
    lc_history = _convert_to_lc_messages(
        state["chat_history"],
        max_messages=10,
    )

    retrieved_context = format_movies_for_context(state["retrieved_movies"])

    messages = [
        SystemMessage(content=ANSWER_SYSTEM_PROMPT),
        *lc_history,
        HumanMessage(
            content=f"""
<latest_user_message>
{state["user_query"]}
</latest_user_message>

<semantic_query>
{state["semantic_query"]}
</semantic_query>

<filters>
genres: {state["genres"]}
excluded_genres: {state["excluded_genres"]}
director: {state["director"]}
year: {state["year"]}
</filters>

<retrieved_movies>
{retrieved_context}
</retrieved_movies>

<task>
Recommend the best matching movies from retrieved_movies.
Use only retrieved_movies.
Answer in Greek.
</task>
"""
        ),
    ]

    response = await llm.ainvoke(messages)

    reply_text = _message_content_to_text(response.content)
    usage_update = _update_usage_state_format(state, response)

    return {
        **state,
        "final_answer": reply_text,
        **usage_update,
    }


# ============================================================
# Graph
# ============================================================

graph = StateGraph(MovieRAGState)

graph.add_node("decide_retrieval", node_decide_retrieval)


graph.add_node("rewrite_query", node_rewrite_query)
graph.add_node("extract_filters", node_extract_filters)
graph.add_node("retrieve_movies", node_retrieve_movies)
graph.add_node("generate_answer", node_generate_answer)

graph.add_node("generate_direct_answer", node_generate_direct_answer)
graph.add_edge(START, "decide_retrieval")
graph.add_conditional_edges(
    "decide_retrieval",
    route_after_decision,
    {
        "needs_retrieval": "rewrite_query",
        "no_retrieval_needed": "generate_direct_answer",
    },
)
graph.add_edge("rewrite_query", "extract_filters")
graph.add_edge("extract_filters", "retrieve_movies")
graph.add_edge("retrieve_movies", "generate_answer")
graph.add_edge("generate_answer", END)
graph.add_edge("generate_direct_answer", END)


print("Graph starts compilation...")
movie_graph_rag_app = graph.compile()
print("Graph compiled successfully.")


# ============================================================
# Main executor used by FastAPI router
# ============================================================

async def run_agent_on_session(
    session_db: Session,
    search_session: SearchSession,
    current_user_id: uuid.UUID,
    user_message: str,
    cost_tracker=None,
) -> str:
    # 1. Load previous memory from DB
    memory_messages = _load_memory_from_session(search_session)

    # 2. Build graph state
    initial_state: MovieRAGState = {
        "user_query": user_message,
        "chat_history": memory_messages,

        "semantic_query": "",
        "rewrite_reasoning": "",

        "genres": [],
        "excluded_genres": [],
        "director": None,
        "year": None,
        "needs_filter": False,
        "filter_reasoning": "",

        "retrieved_movies": [],
        "final_answer": "",

        "usage": _empty_usage(),
        "cost": 0.0,
    }

    # 3. Run graph
    result = await movie_graph_rag_app.ainvoke(initial_state)

    reply_text = result["final_answer"]

    usage = result.get("usage", _empty_usage())
    estimated_cost = result.get("cost", 0.0)

    # 4. Save updated memory
    new_memory = _append_and_trim_memory(
        existing=memory_messages,
        user_message=user_message,
        assistant_message=reply_text,
        max_messages=MAX_MEMORY_MESSAGES,
    )

    _save_memory_to_session(
        session_db=session_db,
        search_session=search_session,
        messages=new_memory,
    )

    # 5. Save query/result to SearchHistory
    _save_search_history(
        session_db=session_db,
        search_session=search_session,
        current_user_id=current_user_id,
        user_message=user_message,
        reply_text=reply_text,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        total_tokens=usage["total_tokens"],
        estimated_cost=estimated_cost,
    )

    if cost_tracker is not None:
        # usage = result.get("usage", _empty_usage())
        cost_tracker.add_request(
            endpoint="/searches/{id}/chat",
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cost=estimated_cost,
        )


    return reply_text



