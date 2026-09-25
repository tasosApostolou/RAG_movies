from datetime import datetime, timezone
from decimal import Decimal
import uuid
from sqlalchemy import Column, DateTime, Numeric, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT
from app.models.user import User

# -----------------------------------------------------------------------------
# Searching agent session schemas and model
# -----------------------------------------------------------------------------



# Base schema: common fields for a search session.
class SearchSessionBase(SQLModel):
    title: str = Field(default="Untitles Search", max_length=255)


# Database model: maps to the `search_session` table.
# Represents one conversation/session of the searching agent for a specific user.
class SearchSession(SearchSessionBase, table=True):
    __tablename__ = "search_session"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: int = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    # Stored as JSON text, for example:
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    # It keeps the conversational memory for this search session.
    # memory: str = Field(default="[]")
    memory: str | None = Field(
    default="[]",
    sa_column=Column(LONGTEXT)
)

    # Timestamps for session lifecycle.
    # timestamps everywhere, prefer get_datetime_utc consistently.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # ORM relationships.
    # owner: the User that owns the session.
    # history: all SearchHistory rows belonging to this session.
    owner: User = Relationship(back_populates="search_sessions")
    history: List["SearchHistory"] = Relationship(
        back_populates="session", cascade_delete=True
    )


# API schema: payload for creating a new search session.
class SearchSessionCreate(SearchSessionBase):
    pass


# API schema: payload for updating a search session.
# Only title is editable here, and it is optional for partial update endpoints.
class SearchSessionUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)


# API response schema: public search session returned to the client.
class SearchSessionPublic(SearchSessionBase):
    id: uuid.UUID
    owner_id: int
    created_at: datetime
    updated_at: datetime


# API response schema: standard list response for search sessions.
class SearchSessionsPublic(SQLModel):
    data: list[SearchSessionPublic]
    count: int


# -----------------------------------------------------------------------------
# Search history schemas and model
# -----------------------------------------------------------------------------


# Base schema: shared fields for a single search/answer entry.
class SearchHistoryBase(SQLModel):
    query: str
    result: Optional[str] = Field(
            default=None,
            sa_column=Column(LONGTEXT, nullable=True),
        )
    
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)

    estimated_cost: Decimal = Field(
        default=Decimal("0.000000"),
        sa_column=Column(Numeric(12, 6), nullable=False),
    )

# Database model: maps to the `search_history` table.
# Represents one user query and the corresponding agent result inside a session.
class SearchHistory(SearchHistoryBase, table=True):
    __tablename__ = "search_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign key to the session where this query belongs.
    session_id: uuid.UUID = Field(
        foreign_key="search_session.id", nullable=False, ondelete="CASCADE"
    )
    # Foreign key to the user who made the query.
    # Keeping owner_id here makes it easier to filter a user's history directly.
    owner_id: int = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ORM relationships for navigation in Python code.
    session: SearchSession = Relationship(back_populates="history")
    owner: User = Relationship()


# API schema: payload for creating a search history entry.
# The client/API layer must specify which session the query belongs to.
class SearchHistoryCreate(SearchHistoryBase):
    session_id: uuid.UUID


# API response schema: public search history entry returned to the client.
class SearchHistoryPublic(SearchHistoryBase):
    id: uuid.UUID
    session_id: uuid.UUID
    owner_id: int
    created_at: datetime


# API response schema: standard list response for search history entries.
class SearchHistoriesPublic(SQLModel):
    data: list[SearchHistoryPublic]
    count: int

class SearchSessionWithHistoryPublic(SearchSessionPublic):
    history: list[SearchHistoryPublic] = []

    
# -----------------------------------------------------------------------------
# Agent chat API schemas
# -----------------------------------------------------------------------------


# API request schema: message sent by the client to the agentic chat endpoint.
class AgentChatRequest(SQLModel):
    message: str


# API response schema: answer returned by the agentic chat endpoint.
class AgentChatResponse(SQLModel):
    session_id: uuid.UUID
    reply: str