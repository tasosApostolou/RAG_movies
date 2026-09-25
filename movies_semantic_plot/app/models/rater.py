# from __future__ import annotations
# from typing import Optional, TYPE_CHECKING
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint
from app.models.user import User

# if TYPE_CHECKING:
#     # from app.models.user import User
#     from app.models.ratings import Rating


class Rater(SQLModel, table=True):
    __tablename__ = "rater"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
    )

    user: Optional["User"] = Relationship(back_populates="rater")
    # user: User = Relationship(back_populates="rater")
    movie_ratings: list["Movie_Rating"] = Relationship(back_populates="rater")






# class Rater(SQLModel, table=True):
#     __tablename__ = "rater"

#     __table_args__ = (
#         UniqueConstraint("user_id", name="uq_rater_user_id"),
#     )

#     id: int | None = Field(default=None, primary_key=True)

#     user_id: int | None = Field(
#         default=None,
#         foreign_key="user.id",
#         nullable=True,
#         index=True,
#     )

#     user: "User | None" = Relationship(back_populates="rater")

#     ratings: list["Rating"] = Relationship(back_populates="rater")