from decimal import Decimal
import uuid
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel import col, delete, func, select

from app.core.rating import get_or_create_rater_for_user, upsert_movie_rating
from app.core.recomender import refresh_hybrid_recommendations_for_user, refresh_recommendations_for_user
from app.dependencies import (
    CurrentAdmin,
    CurrentUser,
    SessionDep,
    get_current_user,
)
from app.core.config import settings
from app.schemas.movie import FavoriteMovieCreate, FavoriteMoviePublic, FavoriteMoviesPublic, GenrePublic, MoviePublic
from app.schemas.user import UserOut
from app.security import verify_password, hash_password
from app.models import User
from app.schemas.user import (
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdate,
    )
from app.models.many_many_links import RecommendedMoviePublic, RecommendedMoviesPublic, UserMovieFavorite, UserMovieRecommendation
from app.models.movie import Movie


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/favorites", response_model=FavoriteMoviePublic)
def add_favorite_movie(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    favorite_in: FavoriteMovieCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    movie = session.get(Movie, favorite_in.movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    existing_favorite = session.get(
        UserMovieFavorite,
        (current_user.id, favorite_in.movie_id),
    )

    rater = get_or_create_rater_for_user(
        session=session,
        user_id=current_user.id,
    )

    upsert_movie_rating(
        session=session,
        rater_id=rater.id,
        movie_id=favorite_in.movie_id,
        stars=Decimal("5.0"), # favorite movie considered as 5 stars rated to calculate user vector collaborative similarity for recoommender system
    )

    if existing_favorite:
        session.commit()

        background_tasks.add_task(
            refresh_hybrid_recommendations_for_user,
            user_id=current_user.id
        )

        return FavoriteMoviePublic(
            user_id=existing_favorite.user_id,
            movie_id=existing_favorite.movie_id,
            created_at=existing_favorite.created_at,
        )

    favorite = UserMovieFavorite(
        user_id=current_user.id,
        movie_id=favorite_in.movie_id,
    )

    session.add(favorite)
    session.commit()
    session.refresh(favorite)

    background_tasks.add_task(
        refresh_recommendations_for_user,
        user_id=current_user.id,
    )

    return FavoriteMoviePublic(
        user_id=favorite.user_id,
        movie_id=favorite.movie_id,
        created_at=favorite.created_at,
    )

# ============================================================
# Get current user's favorites
# ============================================================

@router.get("/favorites", response_model=FavoriteMoviesPublic)
def list_favorite_movies(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    q: Optional[str] = None,
) -> Any:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    statement = (
        select(Movie)
        .join(UserMovieFavorite, UserMovieFavorite.movie_id == Movie.id)
        .where(UserMovieFavorite.user_id == current_user.id)
    )

    count_statement = (
        select(func.count(Movie.id))
        .join(UserMovieFavorite, UserMovieFavorite.movie_id == Movie.id)
        .where(UserMovieFavorite.user_id == current_user.id)
    )

    if q:
        like = f"%{q}%"
        statement = statement.where(Movie.title.like(like))
        count_statement = count_statement.where(Movie.title.like(like))

    count = session.exec(count_statement).one()

    movies = session.exec(
        statement
        .offset(skip)
        .limit(limit)
    ).all()

    return FavoriteMoviesPublic(
        movies=[movie_to_public(movie) for movie in movies],
        # movies=[movie for movie in movies],
        count=count,
    )


@router.get("/recommendations", response_model=RecommendedMoviesPublic)
async  def list_recommended_movies(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> Any:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # refresh_recommendations_for_user(current_user.id,session )

    count_statement = (
        select(func.count(UserMovieRecommendation.id))
        .where(UserMovieRecommendation.user_id == current_user.id)
    )

    count = session.exec(count_statement).one()

    statement = (
        select(Movie, UserMovieRecommendation)
        .join(
            UserMovieRecommendation,
            UserMovieRecommendation.movie_id == Movie.id,
        )
        .where(UserMovieRecommendation.user_id == current_user.id)
        .order_by(UserMovieRecommendation.rank)
        .offset(skip)
        .limit(limit)
    )

    rows = session.exec(statement).all()

    return RecommendedMoviesPublic(
        movies=[
            RecommendedMoviePublic(
                id=movie.id,
                title=movie.title,
                year=movie.year,
                director=movie.director,
                # cast=movie.cast,
                plot=movie.plot,
                score=recommendation.score,
                rank=recommendation.rank,
            )
            for movie, recommendation in rows
        ],
        count=count,
    )    

def movie_to_public(movie: Movie) -> MoviePublic:
    return MoviePublic(
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


# ============================================================
# Remove favorite
# ============================================================

@router.delete(
    "/favorites/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_favorite_movie(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    movie_id: int,
) -> None:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    favorite = session.get(
        UserMovieFavorite,
        (current_user.id, movie_id),
    )

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite movie not found",
        )

    session.delete(favorite)
    session.commit()

    return None




@router.get(
    "/",
    response_model=UsersPublic,
)
def read_users(session: SessionDep,admin:CurrentAdmin, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = (
        select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    )
    users = session.exec(statement).all()

    users_public = [UserPublic.model_validate(user) for user in users]
    return UsersPublic(data=users_public, count=count)



@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdate, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = session.exec(
        select(User).where(User.email == user_in.email)
        ).first()

        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    try:
        for field, value in user_in.model_dump(exclude_unset=True).items():
            setattr(existing_user, field, value)

        session.add(existing_user)
        session.commit()
        session.refresh(existing_user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user") from e

    return current_user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


