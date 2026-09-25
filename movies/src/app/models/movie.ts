export interface GenrePublic {
  id: number;
  name: string;
}

export interface MoviePublic {
  id: number;
  title: string;
  year: number | null;
  director: string | null;
  plot: string | null;
  poster_url: string | null;
  imdb_id: string | null;
  tmdb_id: number | null;
  created_at: string;
  updated_at: string;
  genres: GenrePublic[];
}

export interface MoviesPublic {
  movies: MoviePublic[];
  count: number;
}

export interface RecommendedMoviePublic {
  id: number;
  title: string;
  year: number | null;
  director: string | null;
  cast: string | null;
  plot: string | null;
  score: number;
  rank: number;
}

export interface RecommendedMoviesPublic {
  movies: RecommendedMoviePublic[];
  count: number;
}

export interface MovieCreate {
  title: string;
  year: number | null;
  director: string | null;
  plot: string;
  poster_url: string | null;
  imdb_id: string | null;
  tmdb_id: number | null;
  genre_ids: number[];
}

export interface FavoriteCreate {
  movie_id: number;
}

export interface FavoriteResponse {
  message: string;
}



export interface GenrePublic {
  id: number;
  name: string;
}


export interface MoviesPublic {
  data: MoviePublic[];
  count: number;
}

export interface FavoriteCreate {
  movie_id: number;
}



export interface RecommendedMoviePublic {
  id: number;
  title: string;
  year: number | null;
  director: string | null;
  cast: string | null;
  plot: string | null;
  score: number;
  rank: number;
}

export interface RecommendedMoviesPublic {
  movies: RecommendedMoviePublic[];
  count: number;
}