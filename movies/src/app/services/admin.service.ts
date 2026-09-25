import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DailyUsage,SessionUsageResponse, UsageSummary } from '../models/admin';
import { MoviesPublic,MovieCreate, MoviePublic } from '../models/movie';
import { environment } from '../../environments/environment.development';


const MOVIES = `${environment.apiURL}/movies`
const ADMIN = `${MOVIES}/admin`;


@Injectable({
  providedIn: 'root',
})

export class AdminService {
  private readonly http = inject(HttpClient);
  // private readonly apiUrl = 'http://127.0.0.1:8000/admin';
  

  getMovies(skip = 0, limit = 20, q = ''): Observable<MoviesPublic> {
    let params = new HttpParams()
      .set('skip', skip)
      .set('limit', limit);

    if (q.trim()) {
      params = params.set('q', q.trim());
    }

    return this.http.get<MoviesPublic>(`${MOVIES}`, { params });
  }

  createMovie(movie: MovieCreate): Observable<MoviePublic> {
    return this.http.post<MoviePublic>(`${ADMIN}`, movie);
  }

  deleteMovie(movieId: number): Observable<void> {
    return this.http.delete<void>(`${ADMIN}/${movieId}`);
  }

  getUsageSummary(dateFrom?: string, dateTo?: string): Observable<UsageSummary> {
    let params = new HttpParams();

    if (dateFrom) {
      params = params.set('date_from', dateFrom);
    }

    if (dateTo) {
      params = params.set('date_to', dateTo);
    }

    return this.http.get<UsageSummary>(`${ADMIN}/analytics/summary`, {
      params,
    });
  }

  getDailyUsage(dateFrom?: string, dateTo?: string): Observable<DailyUsage[]> {
    let params = new HttpParams();

    if (dateFrom) {
      params = params.set('date_from', dateFrom);
    }

    if (dateTo) {
      params = params.set('date_to', dateTo);
    }

    return this.http.get<DailyUsage[]>(`${ADMIN}/analytics/daily`, {
      params,
    });
  }

  getSessionUsage(skip = 0, limit = 20): Observable<SessionUsageResponse> {
    const params = new HttpParams()
      .set('skip', skip)
      .set('limit', limit);

    return this.http.get<SessionUsageResponse>(
      `${ADMIN}/analytics/sessions`,
      { params }
    );
  }
}