from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# Genre schemas
# ============================================================

class GenreBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class GenrePublic(GenreBase):
    id: int


class GenresPublic(BaseModel):
    data: list[GenrePublic]
    count: int


# ============================================================
# Movie schemas
# ============================================================

class MovieBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    year: int | None = None
    director: str | None = Field(default=None, max_length=255)
    plot: str | None = None
    poster_url: str | None = Field(default=None, max_length=500)
    imdb_id: str | None = Field(default=None, max_length=50)
    tmdb_id: int | None = None


class MovieCreate(MovieBase):
    """
    Schema movie creation with API.

    """

    genre_ids: list[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    """
    Όλα optional, γιατί σε PATCH μπορείς να αλλάξεις μόνο ένα field.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    year: int | None = None
    director: str | None = Field(default=None, max_length=255)
    plot: str | None = None
    poster_url: str | None = Field(default=None, max_length=500)
    imdb_id: str | None = Field(default=None, max_length=50)
    tmdb_id: int | None = None

    # Αν δοθεί, αντικαθιστά τα genres της ταινίας
    genre_ids: list[int] | None = None


class MoviePublic(MovieBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    genres: list[GenrePublic] = Field(default_factory=list)


class MoviesPublic(BaseModel):
    movies: list[MoviePublic]
    count: int



class MovieWithPlotPublic(MoviePublic):
    plot: str

class MoviePlotPublic(BaseModel):
    id: int
    title: str
    plot: str

# ============================================================
# Favorite movie schemas
# ============================================================

class FavoriteMovieCreate(BaseModel):
    movie_id: int


class FavoriteMoviePublic(BaseModel):
    user_id: int
    movie_id: int
    created_at: datetime


class FavoriteMoviesPublic(BaseModel):
    movies: list[MoviePublic]
    count: int