from typing import Optional

from pydantic import BaseModel, Field



class MovieFiltersOutput(BaseModel):
    genres: list[str] = Field(default_factory=list)
    excluded_genres: list[str] = Field(default_factory=list)
    director: Optional[str] = None
    year: Optional[int] = None
    needs_filter: bool = False
    reasoning: str = ""

class SemanticRewriteOutput(BaseModel):
    semantic_query: str
    reasoning: str = ""    


class RetrievalDecisionOutput(BaseModel):
    needs_retrieval: bool = Field(description="if user asking for find movies")
    reasoning: str = ""