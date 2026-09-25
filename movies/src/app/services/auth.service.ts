import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { jwtDecode  } from 'jwt-decode';
import { JwtPayload, LoginRequest, LoginResponse, RegisterRequest, UserOut } from '../models/login';
import { environment } from '../../environments/environment.development';

const AUTH = `${environment.apiURL}/auth`;

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly http = inject(HttpClient);

  // private readonly apiUrl = 'http://127.0.0.1:8000';
  private readonly tokenKey = 'access_token';

  login(data: LoginRequest): Observable<LoginResponse> {
    const body = new URLSearchParams();

    body.set('username', data.email);
    body.set('password', data.password);

    return this.http
      .post<LoginResponse>(`${AUTH}/login`, body.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      .pipe(
        tap((response) => {
          localStorage.setItem(this.tokenKey, response.access_token);
        })
      );
  }

  register(data: RegisterRequest): Observable<UserOut> {
    return this.http.post<UserOut>(`${AUTH}/register`, data);
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isLoggedIn(): boolean {
    const token = this.getToken();

    if (!token) {
      return false;
    }

    return !this.isTokenExpired();
  }

  getPayload(): JwtPayload | null {
    const token = this.getToken();

    if (!token) {
      return null;
    }

    try {
      return jwtDecode<JwtPayload>(token);
    } catch {
      return null;
    }
  }

  isSuperuser(): boolean {
    const payload = this.getPayload();

    return payload?.is_superuser === true;
  }

  isTokenExpired(): boolean {
    const payload = this.getPayload();

    if (!payload?.exp) {
      return true;
    }

    const nowInSeconds = Math.floor(Date.now() / 1000);

    return payload.exp < nowInSeconds;
  }
}