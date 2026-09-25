from datetime import datetime, timezone
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class MovieGenreLink(SQLModel, table=True):
    __tablename__ = "movie_genre_link"

    movie_id: int | None = Field(
        default=None,
        foreign_key="movie.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    genre_id: int | None = Field(
        default=None,
        foreign_key="genre.id",
        primary_key=True,
        ondelete="CASCADE",
    )


class UserMovieFavorite(SQLModel, table=True):
    __tablename__ = "user_movie_favorite"

    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    movie_id: int | None = Field(
        default=None,
        foreign_key="movie.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        nullable=False,
    )



class UserMovieRecommendation(SQLModel, table=True):
    __tablename__ = "user_movie_recommendation"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
    )

    movie_id: int = Field(
        foreign_key="movie.id",
        nullable=False,
        index=True,
    )

    score: float = Field(nullable=False)
    rank: int = Field(nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


from datetime import datetime
from sqlmodel import SQLModel


class RecommendedMoviePublic(SQLModel):
    id: int
    title: str
    year: int | None = None
    director: str | None = None
    cast: str | None = None
    plot: str | None = None
    score: float
    rank: int


class RecommendedMoviesPublic(SQLModel):
    movies: list[RecommendedMoviePublic]
    count: int    