from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.many_many_links import MovieGenreLink, UserMovieFavorite
# from app.models.ratings import Rating



def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class Movie(SQLModel, table=True):
    __tablename__ = "movie"

    __table_args__ = (
        UniqueConstraint("title", "year", name="uq_movie_title_year"),
    )

    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(
        index=True,
        nullable=False,
        min_length=1,
        max_length=255,
    )

    year: int | None = Field(default=None, index=True)

    director: str | None = Field(default=None, max_length=255)

    plot: str | None = Field(
        default=None,
        sa_column=Column(Text),
    )

    poster_url: str | None = Field(default=None, max_length=500)

    imdb_id: str | None = Field(default=None, index=True, max_length=50)

    tmdb_id: int | None = Field(default=None, index=True)

    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        nullable=False,
    )

    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    genres: list["Genre"] = Relationship(
        back_populates="movies",
        link_model=MovieGenreLink,
    )

    favorited_by_users: list["User"] = Relationship(
        back_populates="favorite_movies",
        link_model=UserMovieFavorite,
    )

    movie_ratings: list["Movie_Rating"] = Relationship(
    back_populates="movie",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )



