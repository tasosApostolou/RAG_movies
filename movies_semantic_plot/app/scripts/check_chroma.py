

from pathlib import Path
from dotenv import load_dotenv
import os

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
CHROMA_DIR = str(ROOT_DIR / "app" / "chroma_movies_db")

load_dotenv(ENV_PATH)

print("CHROMA_DIR:", CHROMA_DIR)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    collection_name="movies",
    embedding_function=embeddings,
)

collection = vectorstore._collection

print("Collection name:", collection.name)

try:
    print("Count:", collection.count())
except Exception as e:
    print("COUNT ERROR:", repr(e))

# try:
#     result = vectorstore.similarity_search("space adventure movie", k=1)
#     print("Search result:", result)
# except Exception as e:
#     print("SEARCH ERROR:", repr(e))

# result = collection.get(
#     limit=10,
#     include=["metadatas", "documents"]
# )

# for metadata in result["metadatas"]:
#     print(metadata.get("movie_id"), metadata.get("title"), metadata.get("doc_type"))

from collections import Counter

result = collection.get(include=["metadatas"])

doc_type_counts = Counter(
    metadata.get("doc_type")
    for metadata in result["metadatas"]
)

print(doc_type_counts)


# #   

# from pathlib import Path
# import chromadb

# ROOT_DIR = Path(__file__).resolve().parents[2]
# CHROMA_DIR = str(ROOT_DIR / "app" / "chroma_movies_db")

# print("CHROMA_DIR:", CHROMA_DIR)

# client = chromadb.PersistentClient(path=CHROMA_DIR)

# collections = client.list_collections()
# print("Collections:", collections)

# collection = client.get_collection("movies")

# print("Collection name:", collection.name)

# try:
#     print("Count:", collection.count())
# except Exception as e:
#     print("COUNT ERROR:", repr(e))

# try:
#     result = collection.peek(limit=1)
#     print("Peek:", result)
# except Exception as e:
#     print("PEEK ERROR:", repr(e))

# try:
#     result = collection.get(limit=1, include=["metadatas", "documents"])
#     print("Get one:", result)
# except Exception as e:
#     print("GET ERROR:", repr(e))

# # app/scripts/check_chroma.py





# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# vector = embeddings.embed_query("test movie plot")
# print(len(vector))


# movie_ids_to_check = [37844, 38798, 42900, 43836, 55247]

# for movie_id in movie_ids_to_check:
#     result = collection.get(
#         where={"movie_id": movie_id},
#         include=["metadatas", "documents"]
#     )

#     print("MovieID:", movie_id)
#     print("Found docs:", len(result["ids"]))

#     for metadata in result["metadatas"]:
#         print(metadata.get("title"), metadata.get("doc_type"))

#     print("-" * 40)