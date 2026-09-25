export interface UsageSummary {
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost: number;
}

export interface DailyUsage {
  day: string;
  requests: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost: number;
}

export interface SessionUsage {
  session_id: string;
  title: string;
  owner_id: number;
  requests: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost: number;
}

export interface SessionUsageResponse {
  data: SessionUsage[];
  count: number;
}


// export interface GenrePublic {
//   id: number;
//   name: string;
// }

// export interface MoviePublic {
//   id: number;
//   title: string;
//   year: number | null;
//   director: string | null;
//   plot: string | null;
//   poster_url: string | null;
//   imdb_id: string | null;
//   tmdb_id: number | null;
//   created_at: string;
//   updated_at: string;
//   genres: GenrePublic[];
// }

// export interface MoviesPublic {
//   data: MoviePublic[];
//   count: number;
// }

// export interface MovieCreate {
//   title: string;
//   year: number | null;
//   director: string | null;
//   plot: string;
//   poster_url: string | null;
//   imdb_id: string | null;
//   tmdb_id: number | null;
//   genre_ids: number[];
// }