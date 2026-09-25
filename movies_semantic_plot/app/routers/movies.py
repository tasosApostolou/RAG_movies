from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import select

from app.dependencies import CurrentAdmin, CurrentUser, SessionDep
from app.models.movie import ( Movie,)
from app.schemas.movie import (    
    GenrePublic,
    MovieCreate,
    MoviePublic,
    MovieWithPlotPublic,
    MoviesPublic,
    MoviePlotPublic,
)
from app.models.conversation import SearchHistory, SearchSession


from app.rag.graph import vectorstore, normalize_key
from app.models.genre import Genre


router = APIRouter(prefix="/movies", tags=["movies"])


def ensure_admin(current_user: CurrentUser) -> None:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


def genres_to_metadata_flags(genres: str | None) -> dict:
    metadata = {}

    if not genres:
        return metadata

    for genre in genres.split(","):
        clean = genre.strip()

        if clean:
            metadata[f"genre_{normalize_key(clean)}"] = True

    return metadata


@router.get("", response_model=MoviesPublic) #
def list_movies(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    q: Optional[str] = None,
) -> Any:
    
    # ensure_admin(current_user)

    statement = select(Movie)

    count_statement = select(func.count(Movie.id))

    if q:
        like = f"%{q}%"
        statement = statement.where(Movie.title.like(like))
        count_statement = count_statement.where(Movie.title.like(like))

    count = session.exec(count_statement).one()

    movies = session.exec(
        statement
        # .order_by(Movie.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    # return movies
    return MoviesPublic(
        movies=[
            MoviePublic(
                id=movie.id,
                title=movie.title,
                year=movie.year,
                director=movie.director,
                plot=movie.plot,
                poster_url=movie.poster_url,
                imdb_id=movie.imdb_id,
                tmdb_id=movie.tmdb_id,
                created_at=movie.created_at,
                updated_at=movie.updated_at,
                genres=[
                    GenrePublic(
                        id=genre.id,
                        name=genre.name,
                    )
                    for genre in movie.genres
                ],
            )
            for movie in movies
        ],
        count=count,
    )


# -------------------------------------------------------------------------
# Movies admin
# -------------------------------------------------------------------------


@router.get("/admin/{movie_id}", response_model=MovieWithPlotPublic)
def get_movie(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    movie_id: int,
) -> Any:
    ensure_admin(current_user)

    movie = session.get(Movie, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return movie


@router.get("/admin/{movie_id}/plot", response_model=MoviePlotPublic)
def get_movie_plot(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    movie_id: int,
) -> Any:
    ensure_admin(current_user)

    movie = session.get(Movie, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return MoviePlotPublic(
        id=movie.id,
        title=movie.title,
        plot=movie.plot,
    )


@router.post(
    "/admin",
    response_model=MovieWithPlotPublic,
    status_code=status.HTTP_201_CREATED,
)
def ingest_movie(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    movie_in: MovieCreate,
) -> Any:
    ensure_admin(current_user)

    movie = Movie.model_validate(movie_in)
    genres = [session.get(Genre, genre_id) for genre_id in movie_in.genre_ids or []]
    movie.genres = [genre for genre in genres if genre is not None]
    movie.updated_at = datetime.utcnow()

    chroma_id: str | None = None

    try:
        session.add(movie)
        session.flush()

        chroma_id = f"movie:{movie.id}"

        vectorstore.add_texts(
            texts=[movie_to_chroma_text(movie)],
            metadatas=[movie_to_chroma_metadata(movie)],
            ids=[chroma_id],
        )

        session.commit()
        session.refresh(movie)

        return movie

    except Exception:
        session.rollback()

        if chroma_id is not None:
            try:
                vectorstore.delete(ids=[chroma_id])
            except Exception:
                pass

        raise


@router.delete("/admin/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    *,
    session: SessionDep,
    current_user: CurrentAdmin,
    movie_id: int,
) -> None:
    ensure_admin(current_user)

    movie = session.get(Movie, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    chroma_id = f"movie:{movie.id}"

    # vectorstore.delete(ids=[chroma_id])

    try:
        # delete all docs(plots,summaries,synthetic queries) of this movie_id  
        vectorstore._collection.delete(
            where={"movie_id": movie_id}
        )
    except Exception:
        
        raise HTTPException(
            status_code=500,
            detail="Movie was not deleted because Chroma delete failed",
        )


    session.delete(movie)
    session.commit()

    return None


# -------------------------------------------------------------------------
# Cost / usage analytics
# -------------------------------------------------------------------------

@router.get("/admin/analytics/summary")
def get_admin_usage_summary(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    ensure_admin(current_user)

    statement = select(
        func.count(SearchHistory.id),
        func.coalesce(func.sum(SearchHistory.input_tokens), 0),
        func.coalesce(func.sum(SearchHistory.output_tokens), 0),
        func.coalesce(func.sum(SearchHistory.total_tokens), 0),
        func.coalesce(func.sum(SearchHistory.estimated_cost), 0),
    )

    if date_from:
        statement = statement.where(
            SearchHistory.created_at >= datetime.combine(date_from, time.min)
        )

    if date_to:
        statement = statement.where(
            SearchHistory.created_at <= datetime.combine(date_to, time.max)
        )

    row = session.exec(statement).one()

    return {
        "total_requests": row[0],
        "total_input_tokens": row[1],
        "total_output_tokens": row[2],
        "total_tokens": row[3],
        "total_cost": float(row[4]),
    }


@router.get("/admin/analytics/daily")
def get_admin_daily_usage(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict]:
    ensure_admin(current_user)

    day_expr = func.date(SearchHistory.created_at)

    statement = select(
        day_expr.label("day"),
        func.count(SearchHistory.id).label("requests"),
        func.coalesce(func.sum(SearchHistory.input_tokens), 0).label("input_tokens"),
        func.coalesce(func.sum(SearchHistory.output_tokens), 0).label("output_tokens"),
        func.coalesce(func.sum(SearchHistory.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(SearchHistory.estimated_cost), 0).label("cost"),
    )

    if date_from:
        statement = statement.where(
            SearchHistory.created_at >= datetime.combine(date_from, time.min)
        )

    if date_to:
        statement = statement.where(
            SearchHistory.created_at <= datetime.combine(date_to, time.max)
        )

    statement = statement.group_by(day_expr).order_by(day_expr)

    rows = session.exec(statement).all()

    return [
        {
            "day": str(row.day),
            "requests": row.requests,
            "input_tokens": row.input_tokens,
            "output_tokens": row.output_tokens,
            "total_tokens": row.total_tokens,
            "cost": float(row.cost),
        }
        for row in rows
    ]


@router.get("/admin/analytics/sessions")
def get_admin_session_usage(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    ensure_admin(current_user)

    statement = (
        select(
            SearchSession.id.label("session_id"),
            SearchSession.title.label("title"),
            SearchSession.owner_id.label("owner_id"),
            func.count(SearchHistory.id).label("requests"),
            func.coalesce(func.sum(SearchHistory.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(SearchHistory.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(SearchHistory.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(SearchHistory.estimated_cost), 0).label("cost"),
        )
        .join(SearchHistory, SearchHistory.session_id == SearchSession.id)
        .group_by(SearchSession.id, SearchSession.title, SearchSession.owner_id)
        .order_by(func.coalesce(func.sum(SearchHistory.estimated_cost), 0).desc())
        .offset(skip)
        .limit(limit)
    )

    rows = session.exec(statement).all()

    count_statement = select(func.count(SearchSession.id))
    count = session.exec(count_statement).one()

    return {
        "data": [
            {
                "session_id": str(row.session_id),
                "title": row.title,
                "owner_id": row.owner_id,
                "requests": row.requests,
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
                "total_tokens": row.total_tokens,
                "cost": float(row.cost),
            }
            for row in rows
        ],
        "count": count,
    }





def get_genre_names(movie: Movie) -> list[str]:
    return [genre.name for genre in movie.genres]


def movie_to_chroma_text(movie: Movie) -> str:
    return movie.plot or ""

def movie_to_chroma_metadata(movie: Movie) -> dict:
    genre_names = [genre.name for genre in movie.genres]

    genres_raw = "|".join(genre_names)

    metadata = {
        "movie_id": int(movie.id),
        "title": movie.title,
        "year": movie.year,
        "director": movie.director or "",
        "doc_type":"summary"
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