# """
# User Model — SQLModel table definition.
# """

from typing import Optional

from sqlmodel import Field, SQLModel
from datetime import datetime, timezone

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING

# if TYPE_CHECKING:
#     from app.models.rater import Rater


# from app.models.conversation import SearchSession
from app.models.many_many_links import UserMovieFavorite


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# User models
# ============================================================

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)

    email: str = Field(
        unique=True,
        index=True,
        nullable=False,
        max_length=255,
    )

    hashed_password: str = Field(nullable=False)

    full_name: str | None = Field(default=None, max_length=255)

    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        nullable=False,
    )

    favorite_movies: list["Movie"] = Relationship(
        back_populates="favorited_by_users",
        link_model=UserMovieFavorite
    )
    search_sessions: list["SearchSession"] = Relationship(
        back_populates="owner", cascade_delete=True
    )

    # rater_id: int | None = Field(
    # default=None,
    # foreign_key="rater.id",
    # nullable=True,
    # )



    rater: "Rater" = Relationship(
    back_populates="user",
    sa_relationship_kwargs={"uselist": False},
)
    



# ============================================================
# Generic auth / message models
# ============================================================

class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

