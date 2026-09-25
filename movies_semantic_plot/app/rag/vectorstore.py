
import os
from pathlib import Path
import re
import chromadb
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import logging

from app.models.movie import Movie


# ROOT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)
if not os.environ.get("OPENAI_API_KEY"):
    import getpass
    os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API key: ")
    
CHROMA_DIR = ROOT_DIR / "app" / "chroma_db"    
# CHROMA_DIR = ROOT_DIR / "app" / "chroma_queries_db"  
# CHROMA_DIR = ROOT_DIR / "app" / "chromatest"    
  

logger = logging.getLogger(__name__)

# ============================================================
# LLM / Vectorstore
# ============================================================

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)

print("Loading Chroma vectorstore...")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
)
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    collection_name="movies",
    embedding_function=embeddings,
)

print("=" * 60)
print("CHROMA COLLECTION DEBUG")
print("=" * 60)

print("start after vecctorstore load")


def vec_movie_to_Chroma(movie):
    
    try:

        vectorstore.add_texts(
            texts=[movie.plot or ""],
            metadatas=[movie_to_chroma_metadata(movie)],
            ids=[f"movie:{movie.id}"],
        )
    except Exception:
        if movie.id is not None:
            try:
                vectorstore.delete(ids=[movie.id])
            except Exception:
                pass
        raise        



def movie_to_chroma_metadata(movie: Movie) -> dict:
    genre_names = [genre.name for genre in movie.genres]

    genres_raw = "|".join(genre_names)

    metadata = {
        "movie_id": int(movie.id),
        "title": movie.title,
        "year": movie.year,
        "director": movie.director or "",
    }

    if genres_raw:
        metadata["genres"] = genres_raw

    for genre in genre_names:
        metadata[f"genre_{normalize_key(genre)}"] = True

    return {
        key: value
        for key, value in metadata.items()
        if value is not None
    }



def normalize_key(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")

def movie_to_chroma_text(movie: Movie) -> str:
    return movie.plot or ""
