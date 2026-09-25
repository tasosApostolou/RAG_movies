import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment.development';
import {
  FavoriteCreate,
  FavoriteResponse,
  MoviesPublic,
  RecommendedMoviesPublic,
} from '../models/movie';

@Injectable({
  providedIn: 'root',
})
export class MovieService {
  private readonly http = inject(HttpClient);

  private readonly moviesUrl = `${environment.apiURL}/movies`;
  private readonly favoritesUrl = `${environment.apiURL}/users/favorites`;

  getMovies(skip = 0, limit = 20, q = ''): Observable<MoviesPublic> {
    let params = new HttpParams()
      .set('skip', skip)
      .set('limit', limit);

    if (q.trim()) {
      params = params.set('q', q.trim());
    }

    return this.http.get<MoviesPublic>(this.moviesUrl, { params });
  }

  addToFavorites(movieId: number): Observable<FavoriteResponse> {
    const body: FavoriteCreate = {
      movie_id: movieId,
    };

    return this.http.post<FavoriteResponse>(this.favoritesUrl, body);
  }

  getFavorites(skip = 0, limit = 20, q = ''): Observable<MoviesPublic> {
    let params = new HttpParams()
      .set('skip', skip)
      .set('limit', limit);

    if (q.trim()) {
      params = params.set('q', q.trim());
    }

    return this.http.get<MoviesPublic>(this.favoritesUrl, { params });
  }

  removeFromFavorites(movieId: number): Observable<void> {
    return this.http.delete<void>(`${this.favoritesUrl}/${movieId}`);
  }


  getRecommendations(skip = 0, limit = 20): Observable<RecommendedMoviesPublic> {
  const params = new HttpParams()
    .set('skip', skip)
    .set('limit', limit);

  return this.http.get<RecommendedMoviesPublic>(
    `${environment.apiURL}/users/recommendations`,
    { params }
  );
}
}
