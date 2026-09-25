import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AgentChatRequest, AgentChatResponse, DeleteSearchResponse, SearchSessionCreate, SearchSessionPublic, SearchSessionsPublic, SearchSessionWithHistoryPublic } from '../models/searchSession';
import { environment } from '../../environments/environment.development';


// 'http://127.0.0.1:8000/searches' 
const SEARCHES = `${environment.apiURL}/searches`; 

@Injectable({
  providedIn: 'root',
})
export class SearchService {
  private readonly http = inject(HttpClient);
  // private readonly apiUrl = 'http://127.0.0.1:8000/searches';

  getSearches(skip = 0, limit = 100): Observable<SearchSessionsPublic> {
    return this.http.get<SearchSessionsPublic>(
      `${SEARCHES}/?skip=${skip}&limit=${limit}`
    );
  }

  getSearchById(sessionId: string): Observable<SearchSessionWithHistoryPublic> {
    return this.http.get<SearchSessionWithHistoryPublic>(
      `${SEARCHES}/${sessionId}`
    );
  }

  createSearch(
    data: SearchSessionCreate = { title: 'New movie search' }
  ): Observable<SearchSessionPublic> {
    return this.http.post<SearchSessionPublic>(`${SEARCHES}/`, data);
  }

  sendMessage(sessionId: string, message: string): Observable<AgentChatResponse> {
    const body: AgentChatRequest = {
      message,
    };

    return this.http.post<AgentChatResponse>(
      `${SEARCHES}/${sessionId}/chat`,
      body
    );
  }

  deleteSearch(sessionId: string): Observable<DeleteSearchResponse> {
    return this.http.delete<DeleteSearchResponse>(
      `${SEARCHES}/${sessionId}`
    );
  }
}

