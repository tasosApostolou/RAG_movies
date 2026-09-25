from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from app.models.many_many_links import MovieGenreLink


class Genre(SQLModel, table=True):
    __tablename__ = "genre"

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(
        unique=True,
        index=True,
        nullable=False,
        min_length=1,
        max_length=100,
    )

    movies: list["Movie"] = Relationship(
        back_populates="genres",
        link_model=MovieGenreLink,
    )