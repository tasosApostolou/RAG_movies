# Imports
import logging
from pathlib import Path
from typing import Any

from fastapi import logger
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.db import get_database
from decimal import Decimal

from sqlmodel import Session, select

from app.models.rater import Rater
from app.models.ratings import Movie_Rating
from app.models.many_many_links import UserMovieFavorite, UserMovieRecommendation
from app.models.user import User
from app.rag import vectorstore

# # from myapp.database import engine
# db = get_database()
# engine = db.engine

ROOT_DIR = Path(__file__).resolve().parents[2]



logger = logging.getLogger(__name__)

def load_ratings_df(session: Session) -> pd.DataFrame:
    df = pd.read_csv(ROOT_DIR / "data/movie_ratings.csv")
    # c = df(columns=)
    # rows = session.exec(
    #     select(
    #         Movie_Rating.rater_id,
    #         Movie_Rating.movie_id,
    #         Movie_Rating.stars,
    #     )
    # ).all()
    # return pd.DataFrame(rows, columns=["rater_id", "movie_id", "stars"])
    # return pd.DataFrame(columns=["RaterID", "MovieID", "Rating"]).rename(columns={"RaterID":"rater_id","MovieID":"movie_id","Rating":"stars"})
    df = pd.read_csv(ROOT_DIR / "data/movie_ratings.csv")
    
    
    df = df[["RaterID", "MovieID", "Rating"]]
  
    df = df.rename(columns={
        "RaterID": "rater_id",
        "MovieID": "movie_id",
        "Rating": "stars"
    })
    
    return df


def create_movie_similarity_df(ratings_df: pd.DataFrame) -> pd.DataFrame:
    if ratings_df.empty:
        return pd.DataFrame()

    movie_matrix = ratings_df.pivot_table(
        index="movie_id",
        columns="rater_id",
        values="stars",
    ).fillna(0)

    similarity = cosine_similarity(movie_matrix)

    return pd.DataFrame(
        similarity,
        index=movie_matrix.index,
        columns=movie_matrix.index,
    )


def recommend_for_rater(
    *,
    rater_id: int,
    ratings_df: pd.DataFrame,
    similarity_df: pd.DataFrame,
    top_n: int = 20,
) -> list[int]:
    user_ratings = ratings_df[ratings_df["rater_id"] == rater_id]

    if user_ratings.empty or similarity_df.empty:
        return []

    liked_movie_ids = set(user_ratings["movie_id"].tolist())

    scores: dict[int, float] = {}

    for _, row in user_ratings.iterrows():
        liked_movie_id = row["movie_id"]
        stars = float(row["stars"])

        if liked_movie_id not in similarity_df.index:
            continue

        similar_movies = similarity_df[liked_movie_id].sort_values(
            ascending=False
        )

        for candidate_movie_id, similarity_score in similar_movies.items():
            if candidate_movie_id in liked_movie_ids:
                continue

            scores[candidate_movie_id] = scores.get(candidate_movie_id, 0.0) + (
                float(similarity_score) * stars
            )

    recommended_movie_ids = [
        movie_id
        for movie_id, _ in sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    return recommended_movie_ids[:top_n]


# def refresh_recommendations_for_user(user_id: int,session:Session = None) -> None:
def refresh_recommendations_for_user(user_id: int) -> None:
    """BAckground task duntion opens new session after commited transaction for user'a favorites appending"""
    db = get_database("mysql")
    engine = db.engine

    logger.info("🔄 Starting refresh_recommendations_for_user for user_id=%s", user_id)
    with Session(engine) as session:
        try:
            rater = session.exec(
                select(Rater).where(Rater.user_id == user_id)
            ).first()

            statement = select(UserMovieFavorite.movie_id).where(UserMovieFavorite.user_id == user_id)

            movie_ids = session.exec(statement).all()

        

            if rater is None:
                logger.info("No rater found for user_id=%s", user_id)
                return

            ratings_df = load_ratings_df(session)
            user_ratings = [{
                # 'rater_id':(ratings_df['rater_id'].max()) + 1,
                'rater_id':rater.id,

                'movie_id':movie_id,
                'stars':5.0,
                # 'Timestamp':pd.Timestamp.now()
                }
                for movie_id in movie_ids]
            ratings_df = pd.concat([ratings_df, pd.DataFrame(user_ratings)], ignore_index=True)



            if ratings_df.empty:
                logger.info("No ratings found")
                return

            similarity_df = create_movie_similarity_df(ratings_df)
            if similarity_df.empty:
                logger.info("Similarity matrix empty")
                return

                # recommended_movie_ids = recommend_for_rater(
                #     rater_id=rater.id,
                #     ratings_df=ratings_df,
                #     similarity_df=similarity_df,
                #     top_n=20,
                # )
                
            recommendations = recommend_for_rater_with_scores(
                rater_id=rater.id,
                ratings_df=ratings_df,
                similarity_df=similarity_df,
                top_n=8,
            )

            if not recommendations:
                logger.info("No recommendations generated for user_id=%s", user_id)
                return
                
            save_recommendations_for_user(
                session=session,
                user_id=user_id,
                recommendations=recommendations,
            )

                # logger.info(
                #     "Generated %s recommendations for user_id=%s",
                #     len(recommended_movie_ids),
                #     user_id,
                # )

            logger.info(
                "Saved %s recommendations for user_id=%s",
                len(recommendations),
                user_id,
            )        

        except Exception as e:
            logger.exception("❌ Error in refresh_recommendations_for_user: %s", e)





def recommend_for_rater_with_scores(
    *,
    rater_id: int,
    ratings_df: pd.DataFrame,
    similarity_df: pd.DataFrame,
    top_n: int = 20,
) -> list[tuple[int, float]]:
    user_ratings = ratings_df[ratings_df["rater_id"] == rater_id]
    if user_ratings.empty or similarity_df.empty:
        return []

    liked_movie_ids = set(user_ratings["movie_id"].tolist())
    scores: dict[int, float] = {}

    for _, row in user_ratings.iterrows():
        liked_movie_id = row["movie_id"]
        stars = float(row["stars"])

        if liked_movie_id not in similarity_df.index:
            continue

        similar = similarity_df[liked_movie_id].sort_values(ascending=False)

        for candidate_movie_id, sim_score in similar.items():
            if candidate_movie_id in liked_movie_ids:
                continue
            scores[candidate_movie_id] = (
                scores.get(candidate_movie_id, 0.0)
                + sim_score
            )

    # Sorted by score and tuple return (movie_id, score)
    sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_items[:top_n]   # list of (movie_id, score)


def save_recommendations_for_user(
    *,
    session: Session,
    user_id: int,
    recommendations: list[tuple[int, float]],   # (movie_id, score)
) -> None:
    # delete old recommendations
    old = session.exec(
        select(UserMovieRecommendation).where(
            UserMovieRecommendation.user_id == user_id
        )
    ).all()
    for rec in old:
        session.delete(rec)

    #  
    for rank, (movie_id, score) in enumerate(recommendations, start=1):
        session.add(
            UserMovieRecommendation(
                user_id=user_id,
                movie_id=movie_id,
                score=score,
                rank=rank,
            )
        )

    session.commit()





def safe_movie_id_from_metadata(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_summary_vectors_from_chroma() -> dict[int, np.ndarray]:
    collection = vectorstore.vectorstore._collection

    result = collection.get(
        where={"doc_type": "summary"},
        include=["embeddings", "metadatas"],
    )

    embeddings = result.get("embeddings")
    metadatas = result.get("metadatas")

    if embeddings is None or metadatas is None:
        return {}

    movie_vectors: dict[int, list[np.ndarray]] = {}

    for embedding, metadata in zip(embeddings, metadatas):
        if metadata is None:
            continue

        movie_id = safe_movie_id_from_metadata(metadata.get("movie_id"))

        if movie_id is None:
            continue

        movie_vectors.setdefault(movie_id, []).append(
            np.array(embedding, dtype=float)
        )

    return {
        movie_id: np.mean(vectors, axis=0)
        for movie_id, vectors in movie_vectors.items()
        if vectors
    }


def calculate_content_scores(
    *,
    favorite_movie_ids: set[int],
    candidate_movie_ids: set[int],
) -> dict[int, float]:
    movie_vectors = load_summary_vectors_from_chroma()

    if not movie_vectors:
        return {}

    favorite_vectors = [
        movie_vectors[movie_id]
        for movie_id in favorite_movie_ids
        if movie_id in movie_vectors
    ]

    if not favorite_vectors:
        return {}

    user_profile_vector = np.mean(favorite_vectors, axis=0).reshape(1, -1)

    content_scores: dict[int, float] = {}

    for movie_id in candidate_movie_ids:
        if movie_id in favorite_movie_ids:
            continue

        movie_vector = movie_vectors.get(movie_id)

        if movie_vector is None:
            continue

        score = cosine_similarity(
            user_profile_vector,
            movie_vector.reshape(1, -1),
        )[0][0]

        content_scores[movie_id] = float(score)

    return content_scores


def calculate_collab_scores_for_rater(
    *,
    rater_id: int,
    ratings_df: pd.DataFrame,
    similarity_df: pd.DataFrame,
) -> dict[int, float]:
    user_ratings = ratings_df[ratings_df["rater_id"] == rater_id]

    if user_ratings.empty or similarity_df.empty:
        return {}

    liked_movie_ids = set(user_ratings["movie_id"].tolist())

    scores: dict[int, float] = {}

    for _, row in user_ratings.iterrows():
        liked_movie_id = row["movie_id"]

        if liked_movie_id not in similarity_df.index:
            continue

        similar = similarity_df[liked_movie_id].sort_values(ascending=False)

        for candidate_movie_id, sim_score in similar.items():
            if candidate_movie_id in liked_movie_ids:
                continue

            scores[candidate_movie_id] = (
                scores.get(candidate_movie_id, 0.0)
                + float(sim_score)
            )

    return scores

def normalize_scores(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}

    values = list(scores.values())
    min_value = min(values)
    max_value = max(values)

    if max_value == min_value:
        return {
            movie_id: 1.0
            for movie_id in scores
        }

    return {
        movie_id: (score - min_value) / (max_value - min_value)
        for movie_id, score in scores.items()
    }


def recommend_for_rater_hybrid_with_scores(
    *,
    rater_id: int,
    ratings_df: pd.DataFrame,
    similarity_df: pd.DataFrame,
    top_n: int = 20,
    collab_weight: float = 0.5,
    content_weight: float = 0.5,
) -> list[tuple[int, float]]:
    user_ratings = ratings_df[ratings_df["rater_id"] == rater_id]

    if user_ratings.empty or similarity_df.empty:
        return []

    favorite_movie_ids = set(user_ratings["movie_id"].tolist())

    collab_scores = calculate_collab_scores_for_rater(
        rater_id=rater_id,
        ratings_df=ratings_df,
        similarity_df=similarity_df,
    )

    candidate_movie_ids = set(collab_scores.keys())

    content_scores = calculate_content_scores(
        favorite_movie_ids=favorite_movie_ids,
        candidate_movie_ids=candidate_movie_ids,
    )

    normalized_collab_scores = normalize_scores(collab_scores)
    normalized_content_scores = normalize_scores(content_scores)

    final_scores: dict[int, float] = {}

    for movie_id in candidate_movie_ids:
        collab_score = normalized_collab_scores.get(movie_id, 0.0)
        content_score = normalized_content_scores.get(movie_id, 0.0)

        final_scores[movie_id] = (
            collab_weight * collab_score
            + content_weight * content_score
        )

    sorted_items = sorted(
        final_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return sorted_items[:top_n]

def refresh_hybrid_recommendations_for_user(user_id: int) -> None:
    """Background task. Opens new session after committed favorite transaction."""
    db = get_database("mysql")
    engine = db.engine

    logger.info("🔄 Starting refresh_recommendations_for_user for user_id=%s", user_id)

    with Session(engine) as session:
        try:
            rater = session.exec(
                select(Rater).where(Rater.user_id == user_id)
            ).first()

            if rater is None or rater.id is None:
                logger.info("No rater found for user_id=%s", user_id)
                return

            statement = (
                select(UserMovieFavorite.movie_id)
                .where(UserMovieFavorite.user_id == user_id)
            )

            movie_ids = session.exec(statement).all()

            if not movie_ids:
                logger.info("No favorite movies found for user_id=%s", user_id)
                return

            ratings_df = load_ratings_df(session)

            user_ratings = [
                {
                    "rater_id": rater.id,
                    "movie_id": movie_id,
                    "stars": 5.0,
                }
                for movie_id in movie_ids
            ]

            ratings_df = pd.concat(
                [ratings_df, pd.DataFrame(user_ratings)],
                ignore_index=True,
            )

            if ratings_df.empty:
                logger.info("No ratings found")
                return

            similarity_df = create_movie_similarity_df(ratings_df)

            if similarity_df.empty:
                logger.info("Similarity matrix empty")
                return

            recommendations = recommend_for_rater_hybrid_with_scores(
                rater_id=rater.id,
                ratings_df=ratings_df,
                similarity_df=similarity_df,
                top_n=8,
                collab_weight=0.5,
                content_weight=0.5,
            )

            if not recommendations:
                logger.info("No recommendations generated for user_id=%s", user_id)
                return

            save_recommendations_for_user(
                session=session,
                user_id=user_id,
                recommendations=recommendations,
            )

            logger.info(
                "Saved %s hybrid recommendations for user_id=%s",
                len(recommendations),
                user_id,
            )

        except Exception as e:
            logger.exception("❌ Error in refresh_recommendations_for_user: %s", e)

# Test
# if __name__ == "__main__":
#     ratings, movies = load_data()
#     similarity_df = create_similarity_matrix(ratings)
#     test_movie = str.lower("back to the future")  # Change this to a title that exists in your database
#     recs = get_recommendations(test_movie, ratings, movies, similarity_df)
#     print(f"Recommendations for '{test_movie}': {recs}")