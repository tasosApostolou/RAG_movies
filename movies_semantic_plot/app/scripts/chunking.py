# import os
# from pathlib import Path
# import re
# import json
# from dotenv import load_dotenv
# import pandas as pd
# from typing import Optional, TypedDict, Any

# from pydantic import BaseModel, Field

# from langchain_core.documents import Document

# from langchain_chroma import Chroma
# import json
# import os
# from pathlib import Path
# import re
# from typing import Any

# from dotenv import load_dotenv
# from pydantic import BaseModel, Field
# from sqlmodel import Session
# from langchain_core.messages import AIMessage, BaseMessage, HumanMessage,SystemMessage
# from langchain_core.documents import Document
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# # ROOT_DIR = Path(__file__).resolve().parent.parent.parent
# ROOT_DIR = Path(__file__).resolve().parents[2]
# print("ROOT DIR: ",ROOT_DIR)
# ENV_PATH = ROOT_DIR / ".env"
# APP_DIR = ROOT_DIR / "app"
# load_dotenv(ENV_PATH)
# # Αν δεν βρεθεί το key (πχ σε Colab), ζητάμε manually
# if not os.environ.get("OPENAI_API_KEY"):
#     import getpass
#     os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API key: ")

# # CHROMA_DIR = str(ROOT_DIR / "chroma_movies_db")
# CHROMA_DIR = APP_DIR / "chroma_movies_db"

# ###################
# OUTPUT_CSV = Path(ROOT_DIR / "last_docs_complete.csv")
# FAILED_CSV = Path(ROOT_DIR / "last_docs_failed.csv")

# def append_row_to_csv(row: dict, path: Path):
#     pd.DataFrame([row]).to_csv(
#         path,
#         mode="a",
#         index=False,
#         header=not path.exists(),
#         encoding="utf-8-sig"
#     )
# ###################

# def safe_str(value: Any) -> str:
#     if pd.isna(value):
#         return ""
#     return str(value).strip()


# def normalize_key(value: str) -> str:
#     value = value.lower().strip()
#     value = re.sub(r"[^a-z0-9]+", "_", value)
#     return value.strip("_")


# def split_plot_into_paragraphs(plot: str) -> list[str]:
#     plot = plot.replace("\r\n", "\n").replace("\r", "\n").strip()

#     # If blank lines,then paragraph breaks
#     if re.search(r"\n\s*\n", plot):
#         paragraphs = re.split(r"\n\s*\n", plot)
#     else:
#         # Else each newline considered as paragraph break
#         paragraphs = plot.split("\n")

#     return [
#         p.strip()
#         for p in paragraphs
#         if p.strip()
#     ]


# def build_paragraph_chunks_df(docs_df: pd.DataFrame) -> pd.DataFrame:
#     rows = []

#     # Κρατάω μόνο full_plot documents
#     full_plot_df = docs_df[docs_df["doc_type"] == "full_plot"].copy()

#     for _, row in full_plot_df.iterrows():
#         plot = safe_str(row.get("page_content", ""))

#         if not plot or plot.lower() == "nan":
#             continue

#         movie_id = int(row["movie_id"])
#         title = safe_str(row.get("title", ""))
#         year = int(row["year"]) if pd.notna(row.get("year")) and safe_str(row.get("year", "")) else None

#         genres_raw = safe_str(row.get("genres", ""))
#         director = safe_str(row.get("director", ""))
#         source_movie = safe_str(row.get("source_movie", ""))
#         source_chroma_id = safe_str(row.get("chroma_id", ""))

#         chunks = split_plot_into_paragraphs(plot)

#         for chunk_index, chunk_text in enumerate(chunks):
#             if not chunk_text:
#                 continue

#             rows.append({
#                 "movie_id": movie_id,
#                 "title": title,
#                 "year": year,
#                 "genres": genres_raw,
#                 "director": director,
#                 "source_movie": source_movie,
#                 "source_chroma_id": source_chroma_id,
#                 "doc_type": "chunk_par",
#                 "chunk_index": chunk_index,
#                 "page_content": chunk_text,
#             })

#     return pd.DataFrame(rows)
# def build_documents_from_chunked_df(chunked_df: pd.DataFrame) -> list[Document]:
#     documents = []

#     for idx, row in chunked_df.iterrows():
#         content = safe_str(row.get("page_content", ""))

#         if not content or content.lower() == "nan":
#             continue

#         movie_id = int(row["movie_id"])
#         title = safe_str(row.get("title", ""))
#         year = int(row["year"]) if pd.notna(row.get("year")) and safe_str(row.get("year", "")) else None

#         genres_raw = safe_str(row.get("genres", ""))
#         genres = [g.strip() for g in genres_raw.split("|") if g.strip()]

#         chunk_index = int(row["chunk_index"])

#         metadata = {
#             "movie_id": movie_id,
#             "title": title,
#             "genres": genres_raw,
#             "year": year,
#             "director": safe_str(row.get("director", "")),
#             "source_movie": safe_str(row.get("source_movie", "")),
#             "source_chroma_id": safe_str(row.get("source_chroma_id", "")),
#             "doc_type": "chunk_par",
#             "chunk_index": chunk_index,
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
#     docs_df = pd.read_csv(ROOT_DIR / "data/chroma_chunk_paragraphs.csv")

#     docs = build_documents_from_chunked_df(docs_df)
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
#     ids = [
#     f"movie_{doc.metadata['movie_id']}_{doc.metadata['doc_type']}_{doc.metadata['chunk_index']}"
#     for doc in docs
# ]

#     batch_size = 500

#     print("Unique ids:", len(set(ids)))
#     print("Total ids:", len(ids))

#     if len(set(ids)) != len(ids):
#         print("WARNING: You have duplicate ids!")

#     batch_size = 500

#     for start_idx in range(0, len(docs), batch_size):
#         batch_docs = docs[start_idx:start_idx + batch_size]
#         batch_ids = ids[start_idx:start_idx + batch_size]

#         vectorstore.add_documents(
#             documents=batch_docs,
#             ids=batch_ids,
#         )

#         print(
#             f"Added batch {start_idx} - {start_idx + len(batch_docs)} | "
#             f"Current count: {vectorstore._collection.count()}"
#         )

#     after_count = vectorstore._collection.count()
#     print("Count after add:", after_count)
#     print("Added:", after_count - before_count)
#     print("Vectorstore persisted to:", CHROMA_DIR)
        
    
# if __name__ == "__main__":
#     main()    