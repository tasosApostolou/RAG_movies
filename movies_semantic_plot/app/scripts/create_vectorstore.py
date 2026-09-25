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
# CHROMA_DIR = APP_DIR / "chroma_queries_db"
CHROMA_DIR = APP_DIR / "chroma_db"

###################
# OUTPUT_CSV = Path(ROOT_DIR / "last_docs_complete.csv")
# FAILED_CSV = Path(ROOT_DIR / "last_docs_failed.csv")

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





def build_documents(docs_df: pd.DataFrame) -> list[Document]:
    documents = []
    chroma_ids = []

    for idx, row in docs_df.iterrows():
        content = safe_str(row.get("page_content", ""))

        if not content or content.lower() == "nan":
            continue

        movie_id = int(row["movie_id"])
        doc_type = safe_str(row.get("doc_type","no_type"))
        # chroma_id = safe_str(row.get("chroma_id", f"{idx}_{doc_type}"))
        chroma_id = safe_str(f"{idx}_{doc_type}")
        
        title = safe_str(row.get("title", ""))
        year = int(row["year"]) if pd.notna(row.get("year")) else None

        genres_raw = safe_str(row.get("genres", ""))
        genres = [g.strip() for g in genres_raw.split("|") if g.strip()]

        metadata = {
            # "chroma_id": chroma_id,
            "movie_id": movie_id,
            "title": title,
            "genres": genres_raw, # only for display, not for filter
            "year": year,
            "director": safe_str(row.get("director", "")),
            "source_movie": safe_str(row.get("source_movie","")),
            "doc_type":doc_type,
        }


# ========= Building genres for genre filtering search =================== #

        for genre in genres:
            metadata[f"genre_{normalize_key(genre)}"] = True

        metadata = {k: v for k, v in metadata.items() if v is not None}

        documents.append(
            Document(
                page_content=content,
                metadata=metadata,
            )
        )

        chroma_ids.append(chroma_id)

        if idx % 50 == 0:
            print(f"Processed row {idx}, documents so far: {len(documents)}")

    return documents,chroma_ids


def main():
    docs_df = pd.read_csv(ROOT_DIR / "data/without_chunks.csv")
    print(docs_df.head())

    docs,chroma_ids = build_documents(docs_df)

    print("Rows in CSV:", len(docs_df))
    print("Documents built:", len(docs))
    print("First doc:", docs[0] if docs else "NO DOCS")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name="movies",
        embedding_function=embeddings,
    )

        
########
    before_count = vectorstore._collection.count()
    print("Count before add:", before_count)

    # ids = [
    #     doc.metadata['chroma_id']
    #     for doc in docs
    # ]

    print("Unique ids:", len(set(chroma_ids)))
    print("Total ids:", len(chroma_ids))

    if len(set(chroma_ids)) != len(chroma_ids):
        print("WARNING: You have duplicate ids!")

    batch_size = 500

    for start_idx in range(0, len(docs), batch_size):
        batch_docs = docs[start_idx:start_idx + batch_size]
        batch_ids = chroma_ids[start_idx:start_idx + batch_size]

        vectorstore.add_documents(
            documents=batch_docs,
            ids=batch_ids,
        )

        print(
            f"Added batch {start_idx} - {start_idx + len(batch_docs)} | "
            f"Current count: {vectorstore._collection.count()}"
        )

    after_count = vectorstore._collection.count()
    print("Count after add:", after_count)
    print("Added:", after_count - before_count)
    print("Vectorstore persisted to:", CHROMA_DIR)

if __name__ == "__main__":
    main()
    
    #docker compose --profile tools run --rm create_vectorstore
    


#         SystemMessage(
#             content=(
#                 """You summarize movie plots for a semantic movie search system using plots of a wiki dataset.

#                 Rules:
#                 - Keep the summary factual, concise, and retrieval-friendly.
#                 -Include the main premise, important characters, setting,   conflict, themes, and distinctive story elements.
#                 - Do not add information that is not in the plot.
#                 - User can ask semantic both english or greek but the full plot context that you have to summarize is only in english.
#                 - Write summary in english.
                
#                 Task:
#                 -You have to summarize movie plots for a semantic movie search system. 
#                 - soundtrack,vibe, atmosphere,mood, plot, and themes are semantic search content. If you can recognize something from the context, include it in your summary for semantic search as the examples. Examples is not constraint for your recognize style etc, but is only to understand the meaning of what you have to recognize and inlude like atmosphere mood of anything you know regardless only with the given tags. For example if you recognize visual style in context, you have too include it.

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








