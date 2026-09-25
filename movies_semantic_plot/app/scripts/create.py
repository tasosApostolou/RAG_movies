import os
from pathlib import Path
import re
import json
from dotenv import load_dotenv
import pandas as pd
from typing import Optional, TypedDict, Any

from pydantic import BaseModel, Field

from langchain_core.documents import Document

from langchain_chroma import Chroma
import json
import os
from pathlib import Path
import re
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlmodel import Session
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage,SystemMessage
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = Path(__file__).resolve().parents[2]
print("ROOT DIR: ",ROOT_DIR)

ENV_PATH = ROOT_DIR / ".env"
APP_DIR = ROOT_DIR / "app"
load_dotenv(ENV_PATH)
# Αν δεν βρεθεί το key (πχ σε Colab), ζητάμε manually
if not os.environ.get("OPENAI_API_KEY"):
    import getpass
    os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API key: ")

# CHROMA_DIR = str(ROOT_DIR / "chroma_movies_db")
CHROMA_DIR = APP_DIR / "chroma_movies_db"

###################
OUTPUT_CSV = Path(ROOT_DIR / "query_general.csv")
FAILED_CSV = Path(ROOT_DIR / "query_general_failed.csv")

def append_row_to_csv(row: dict, path: Path):
    pd.DataFrame([row]).to_csv(
        path,
        mode="a",
        index=False,
        header=not path.exists(),
        encoding="utf-8-sig"
    )
###################

def safe_str(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_key(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


# def build_movie_documents(movies_df: pd.DataFrame) -> list[Document]:
#     documents = []

#     for _, row in movies_df.iterrows():
#         plot = str(row.get("Plot", "")).strip()

#         if not plot or plot.lower() == "nan":
#             continue

#         genres_raw = str(row.get("Genres", "")).strip()
#         genres = [g.strip() for g in genres_raw.split("|") if g.strip()]
        

#         metadata = {
#             "movie_id": int(row["MovieID"]),
#             "title": str(row.get("Title", "")),
#             "genres": genres_raw,
#             "year": int(row["Year"]) if pd.notna(row.get("Year")) else None,
#             "director": str(row.get("Director", "")),
#             # "cast": str(row.get("Cast", "")),
#         }

#         # Boolean genre flags για Chroma filtering
#         for genre in genres:
#             metadata[f"genre_{normalize_key(genre)}"] = True

#         # Αφαίρεση None γιατί μπορεί να δημιουργήσει θέμα στο Chroma
#         metadata = {k: v for k, v in metadata.items() if v is not None}

#         documents.append(
#             Document(
#                 page_content=plot,
#                 metadata=metadata
#             )
#         )

#     return documents


# def create_movie_vectorstore(movies_df: pd.DataFrame) -> Chroma:
#     embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

#     return Chroma.from_documents(
#         documents=build_movie_documents(movies_df),
#         embedding=embeddings,
#         persist_directory=CHROMA_DIR,
#         collection_name="movies",
#     )





# # def build_movie_documents(movies_df: pd.DataFrame) -> list[Document]:
# #     documents = []

# #     for _, row in movies_df.iterrows():
# #         plot = safe_str(row.get("Plot", ""))

# #         if not plot or plot.lower() == "nan":
# #             continue

# #         genres_raw = safe_str(row.get("Genres", ""))
# #         genres = [g.strip() for g in genres_raw.split("|") if g.strip()]

# #         metadata = {
# #             "movie_id": int(row["MovieID"]),
# #             "title": safe_str(row.get("Title", "")),
# #             "genres": genres_raw, 
# #             "year": int(row["Year"]) if pd.notna(row.get("Year")) else 0, #  
# #             "director": safe_str(row.get("Director", "")),
# #             "cast": safe_str(row.get("Cast", "")),
# #         }

# #         # Μόνο τα genres που υπάρχουν μπαίνουν ως True.
# #         # Δεν βάζουμε genre_x=False για τα υπόλοιπα.
# #         for genre in genres:
# #             metadata[f"genre_{normalize_key(genre)}"] = True

# #         documents.append(
# #             Document(
# #                 page_content=plot,
# #                 metadata=metadata,
# #             )
# #         )

# #     return documents

# def main():
#     movies_df = pd.read_csv(ROOT_DIR / "data/movies_plots.csv")
#     print(movies_df.head())

#     docs = build_movie_documents(movies_df)

#     print("Rows in CSV:", len(movies_df))
#     print("Documents built:", len(docs))
#     print("First doc:", docs[0] if docs else "NO DOCS")

#     print("create vectorstore is running...")

#     vectorstore = Chroma.from_documents(
#         documents=docs,
#         embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
#         persist_directory=str(CHROMA_DIR),
#         collection_name="movies",
#     )
#     collections = vectorstore._client.list_collections()
#     print("Collections after creation:", collections) 

#     print("Count immediately after creation:", vectorstore._collection.count())
#     print("Vectorstore persisted to:", CHROMA_DIR)


# if __name__ == "__main__":
#     main()

# # python -m app.scripts.create_vectorstore
#########################################################
#########################################################


def build_movie_documents_with_summaries(movies_df: pd.DataFrame) :
    documents = []

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.18,
    )

    for idx, row in movies_df.iterrows():
        # plot = safe_str(row.get("Plot", ""))
        plot = safe_str(row.get("page_content", ""))
        

        if not plot or plot.lower() == "nan":
            continue

        # movie_id = int(row["MovieID"])
        movie_id = int(row["movie_id"])
        # title = safe_str(row.get("Title", ""))
        title = safe_str(row.get("title", ""))
        # year = int(row["Year"]) if pd.notna(row.get("Year")) else None        
        year = int(row["year"]) if pd.notna(row.get("year")) else None

        # genres_raw = safe_str(row.get("Genres", ""))
        genres_raw = safe_str(row.get("genres", ""))     
        # genres = [g.strip() for g in genres_raw.split("|") if g.strip()]

        # base_metadata = {
        #     "movie_id": movie_id,
        #     "title": title,
        #     "genres": genres_raw,
        #     "year": year,
        #     # "director": safe_str(row.get("Director", "")),
        #     "director": safe_str(row.get("director", "")),            
        # }

        # for genre in genres:
        #     base_metadata[f"genre_{normalize_key(genre)}"] = True

        # base_metadata = {k: v for k, v in base_metadata.items() if v is not None}

        # query = plot

        # # 1. Full plot document
        # full_plot_metadata = {
        #     **base_metadata,
        #     "doc_type": "full_plot",
        # }

        # documents.append(
        #     Document(
        #         page_content=plot,
        #         metadata=full_plot_metadata,
        #     )
        # )

        #################################################
        # 2. query document############################
        try:
            query = generate_query(
                llm=llm,
                title=title,
                year=year,
                plot=plot,
            )

            query_row = {
                "chroma_id": None,  # Δεν υπάρχει ακόμα στη Chroma
                "movie_id": movie_id,
                # "source_movie": f"{movie_id}|{title}",
                "page_content": query,
                "genres": safe_str(row.get("genres", "")),
                "director":safe_str( row.get("director", "")),
                "title": title,
                "year": year,
                "doc_type": f"{row.get("doc_type", "")}_semantic_query",
            }

            append_row_to_csv(query_row, OUTPUT_CSV)
            print(f"Saved query for MovieID={movie_id}")
            
        except Exception as e:
            print(f"query failed for MovieID={movie_id}, Title={title}: {e}")

            failed_row = {
            "movie_id": movie_id,
            "title": title,
            "year": year,
            "error": repr(e),
        }

            append_row_to_csv(failed_row, FAILED_CSV)

            print(f"FAILED MovieID={movie_id}, Title={title}: {e}")
          
            continue





    #     query_metadata = {
    #         **base_metadata,
    #         "doc_type": "query"
    #         # "source_movie": f"{movie_id}|{title}",
    #     }

    #     documents.append(
    #         Document(
    #             page_content=query,
    #             metadata=query_metadata,
    #         )
    #     )

    #     if idx % 50 == 0:
    #         print(f"Processed row {idx}, documents so far: {len(documents)}")

#     # return documents
SYSTEM_PROMPT = """
You generate synthetic movie-search questions for a movie recommendation RAG system.
Users search movies using natural-language queries. Users may search in English or Greek, but the plot you receive is in English and your synthetic question must be written in English.

Your job:
Given one plot chunk from a movie, write ONE natural user question that this chunk could answer.

The question should sound like something a user might ask when searching for a movie by description, plot, themes, atmosphere, mood, conflict, visuals, character situation, emotional tone, genre elements, or narrative premise.

# The synthetic query should help with search intents like:
#                 - 'can you find me a Sci-fi detective movie with philosophical themes?'
#                 - 'Ταινία με διαστημικό ταξίδι όπου ο χρόνος κυλάει διαφορετικά' (Plot-based query)
#                 - 'Movies with neon visuals and synth soundtrack' (Cinematic style query)
#                 - 'Sci-fi detective movie with philosophical themes'(implementation with filter search)
#                 - 'Ταινίες που προκαλούν anxiety και tension συνεχώς'(Psychological/emotional)
#                 - 'Χαρούμενες ταινίες για να δω όταν είμαι πεσμένος' (Vibe Queries)
#                 - 'Σκοτεινές και ανατριχιαστικές ταινίες ψυχολογικού τρόμου'
#                 - 'Θέλω σκοτεινή sci-fi ταινία με υπαρξιακά θέματα'  

# Examples above is NOT constraint and are not meant to be followed closely. Is only to understand as a part of semantic signals that may be useful for retrieval. Do NOT invent such details unless they are supported by the provided plot and also do NOT miss and NOT skip semantic details even are absent from the above examples. Soundtrack,vibe, atmosphere,mood, plot,themes etc constitute semantic search content

Important rules:
- Use ONLY information clearly present or strongly implied in the plot.
- Do NOT invent facts, genres, themes, emotions, visuals, or political/psychological meanings that are not supported by the plot.
- The question must be answerable from this plot alone.
- Do NOT mention the movie title.
- Prefer a question that is specific enough to retrieve this movie/plot, but general enough to sound like a real search query.
- It may refer to plot, conflict, characters, setting, tone, atmosphere, emotional mood, visual style, or thematic ideas, but only when supported by the plot.
- Do not force mood/atmosphere/themes if the plot is mainly plot-based.
- Output only the generated question.

Bad Queries examples that you dont generate:
-   Bad query: 'What happens in The Matrix when Neo takes the red pill?'
    reason: includes title,names
    Good queries: ["sci-fi movie has a hacker discover that reality is a simulation after choosing between tow pills", "sci-fi movie with machine control, simulation betrayal, conflict and psychological temptation"]
    
"""

#################################################################
#################################################################
def generate_query(llm: ChatOpenAI, title: str, year: Any, plot: str) -> str:
    messages = [
        SystemMessage(
            content=(SYSTEM_PROMPT)  
        ),
        HumanMessage(
            content=(
                f"Movie: {title} ({year})\n\n"
                f"Plot:\n{plot}\n\n"
                "Write a concise semantic query based on plot"
            )
        ),
    ]

    response = llm.invoke(messages)
    return response.content.strip()
################################################################################
################################################################################



def main():
    movies_df = pd.read_csv(ROOT_DIR / "data/chroma_clean.csv")
    print(movies_df.head())

    # docs = build_movie_documents_with_summaries(movies_df)
    build_movie_documents_with_summaries(movies_df)

    # docs = build_query_documents(movies_df)
    # print("Rows in CSV:", len(movies_df))
    # print("Documents built:", len(docs))
    # print("First doc:", docs[0] if docs else "NO DOCS")

    # print("create vectorstore is running...")
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # vectorstore = Chroma.from_documents(
    #     documents=docs,
    #     embedding=embeddings
    #     persist_directory=str(CHROMA_DIR),
    #     collection_name="movies",
    # )
    # collections = vectorstore._client.list_collections()
    # print("Collections after creation:", collections) 

    # print("Count immediately after creation:", vectorstore._collection.count())
    # print("Vectorstore persisted to:", CHROMA_DIR)


if __name__ == "__main__":
    main()
##########################################################





# def build_documents(docs_df: pd.DataFrame) -> list[Document]:
#     documents = []

#     for idx, row in docs_df.iterrows():
#         content = safe_str(row.get("page_content", ""))

#         if not content or content.lower() == "nan":
#             continue

#         movie_id = int(row["movie_id"])
#         title = safe_str(row.get("title", ""))
#         year = int(row["year"]) if pd.notna(row.get("year")) else None

#         genres_raw = safe_str(row.get("genres", ""))
#         genres = [g.strip() for g in genres_raw.split("|") if g.strip()]

#         metadata = {
#             "movie_id": movie_id,
#             "title": title,
#             "genres": genres_raw,
#             "year": year,
#             "director": safe_str(row.get("director", "")),
#             "source_movie": safe_str(row.get("source_movie","")),
#             "doc_type":safe_str(row.get("doc_type","")),
#         }

#         for genre in genres:
#             metadata[f"genre_{normalize_key(genre)}"] = True

#         metadata = {k: v for k, v in metadata.items() if v is not None}

#         documents.append(
#             Document(
#                 page_content=content,
#                 metadata=metadata,
#             )
#         )

#         if idx % 50 == 0:
#             print(f"Processed row {idx}, documents so far: {len(documents)}")

#     return documents


# def main():
#     docs_df = pd.read_csv(ROOT_DIR / "data/last_complete_movies.csv")
#     print(docs_df.head())

#     docs = build_documents(docs_df)

#     print("Rows in CSV:", len(docs_df))
#     print("Documents built:", len(docs))
#     print("First doc:", docs[0] if docs else "NO DOCS")

#     embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

#     vectorstore = Chroma(
#         persist_directory=str(CHROMA_DIR),
#         collection_name="movies",
#         embedding_function=embeddings,
#     )

#     before_count = vectorstore._collection.count()
#     print("Count before add:", before_count)

#     ids = [
#         f"movie_{doc.metadata['movie_id']}_{doc.metadata['doc_type']}"
#         for doc in docs
#     ]

#     vectorstore.add_documents(
#         documents=docs,
#         ids=ids,
#     )

#     after_count = vectorstore._collection.count()
#     print("Count after add:", after_count)
#     print("Added:", after_count - before_count)
#     print("Vectorstore persisted to:", CHROMA_DIR)


# if __name__ == "__main__":
#     main()


#         SystemMessage(
#             content=(
#                 """You summarize movie plots for a semantic movie search system using plots of a wiki dataset.

#                 Rules:
#                 - Keep the query factual, concise, and retrieval-friendly.
#                 -Include the main premise, important characters, setting,   conflict, themes, and distinctive story elements.
#                 - Do not add information that is not in the plot.
#                 - User can ask semantic both english or greek but the full plot context that you have to summarize is only in english.
#                 - Write query in english.
                
#                 Task:
#                 -You have to summarize movie plots for a semantic movie search system. 
#                 - soundtrack,vibe, atmosphere,mood, plot, and themes are semantic search content. If you can recognize something from the context, include it in your query for semantic search as the examples. Examples is not constraint for your recognize style etc, but is only to understand the meaning of what you have to recognize and inlude like atmosphere mood of anything you know regardless only with the given tags. For example if you recognize visual style in context, you have too include it.

#                 Some examples that users can be sarch about movies is:
#                 **can you find me a Sci-fi detective movie with philosophical themes?**
#                 **Ταινία με διαστημικό ταξίδι όπου ο χρόνος κυλάει διαφορετικά" (Plot-based query)**
#                 **Movies with neon visuals and synth soundtrack"(Cinematic style query)**
#                 **Sci-fi detective movie with philosophical themes" (implementation with filter search)**
#                 **Ταινίες που προκαλούν anxiety και tension συνεχώς",(Psychological/emotional)**
#                 **Χαρούμενες ταινίες για να δω όταν είμαι πεσμένος",(Vibe Queries)**
#                 **Σκοτεινές και ανατριχιαστικές ταινίες ψυχολογικού τρόμου**
#                 **Θέλω σκοτεινή sci-fi ταινία με υπαρξιακά θέματα**   

         
                
# """
#             )







