
from typing import Optional, TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from app.models.movie import Movie
from app.models.rater import Rater

# if TYPE_CHECKING:
#     from app.models.rater import Rater
#     from app.models.movie import Movie


class Movie_Rating(SQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)

    rater_id: int = Field(
        foreign_key="rater.id",
        nullable=False,
        index=True,
    )

    movie_id: int = Field(
        foreign_key="movie.id",
        nullable=False,
        index=True,
    )

    stars: Decimal = Field(nullable=False)

    rater: Rater = Relationship(back_populates="movie_ratings")
    movie: Movie = Relationship(back_populates="movie_ratings")


