import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AuthService } from '../../services/auth.service';
import {
  AgentChatResponse,
  // SearchService,
  SearchSessionPublic,
  SearchSessionWithHistoryPublic,
} from '../../models/searchSession';
import { SearchService } from '../../services/search.service';
import { HttpErrorResponse } from '@angular/common/http';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, DatePipe],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css',
})
export class SearchComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly searchService = inject(SearchService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  sessions: SearchSessionPublic[] = [];
  activeSession: SearchSessionWithHistoryPublic | null = null;

  messages: ChatMessage[] = [];

  isLoadingSessions = false;
  isLoadingConversation = false;
  isCreatingSession = false;
  isSendingMessage = false;

  deletingSessionId: string | null = null;

  errorMessage = '';

  chatForm = this.fb.nonNullable.group({
    message: ['', [Validators.required]],
  });

  ngOnInit(): void {
    this.loadSessions();
  }

  loadSessions(): void {
    this.isLoadingSessions = true;
    this.errorMessage = '';

    this.searchService.getSearches().subscribe({
      next: (response) => {
        this.sessions = response.data;

        if (this.sessions.length > 0) {
          this.selectSession(this.sessions[0].id);
        }
      },
      error: () => {
        this.errorMessage = 'Could not load your search sessions.';
        this.isLoadingSessions = false;
      },
      complete: () => {
        this.isLoadingSessions = false;
      },
    });
  }

  createNewSearch(): void {
    this.isCreatingSession = true;
    this.errorMessage = '';

    this.searchService
      .createSearch({
        title: 'New movie search',
      })
      .subscribe({
        next: (session) => {
          this.sessions = [session, ...this.sessions];
          this.selectSession(session.id);
        },
        error: () => {
          this.errorMessage = 'Could not create a new search session.';
          this.isCreatingSession = false;
        },
        complete: () => {
          this.isCreatingSession = false;
        },
      });
  }

  selectSession(sessionId: string): void {
    this.isLoadingConversation = true;
    this.errorMessage = '';

    this.searchService.getSearchById(sessionId).subscribe({
      next: (sessionWithHistory) => {
        this.activeSession = sessionWithHistory;
        this.messages = this.mapHistoryToMessages(sessionWithHistory);
      },
      error: () => {
        this.errorMessage = 'Could not load this conversation.';
        this.isLoadingConversation = false;
      },
      complete: () => {
        this.isLoadingConversation = false;
      },
    });
  }

  private mapHistoryToMessages(
    session: SearchSessionWithHistoryPublic
  ): ChatMessage[] {
    const messages: ChatMessage[] = [];

    for (const historyItem of session.history) {
      messages.push({
        role: 'user',
        content: historyItem.query,
      });

      if (historyItem.result) {
        messages.push({
          role: 'assistant',
          content: historyItem.result,
        });
      }
    }

    if (messages.length === 0) {
      messages.push({
        role: 'assistant',
        content:
          'Describe the kind of movie you are looking for. I will search semantically through the movie plot database.',
      });
    }

    return messages;
  }

  sendMessage(): void {
    if (!this.activeSession) {
      this.errorMessage = 'Create a search session first.';
      return;
    }

    if (this.chatForm.invalid) {
      this.chatForm.markAllAsTouched();
      return;
    }

    const message = this.chatForm.getRawValue().message.trim();

    if (!message) {
      return;
    }

    this.messages.push({
      role: 'user',
      content: message,
    });

    this.chatForm.reset();
    this.isSendingMessage = true;
    this.errorMessage = '';

    this.searchService.sendMessage(this.activeSession.id, message).subscribe({
      next: (response: AgentChatResponse) => {
        this.messages.push({
          role: 'assistant',
          content: response.reply,
        });

        /*
          refresh session to synchronize local UI
           with history writen in db.
        */
        this.refreshActiveSessionSilently();
      },
      error: (err: HttpErrorResponse) => {
        let backendMessage = 'Something went wrong while searching. Please try again.';
        if (err.error && err.error.message) {
          backendMessage = err.error.message;
        }

        this.errorMessage = backendMessage;

        this.messages.push({
          role: 'assistant',
          content: "Backend error message:" + backendMessage,
        });

        this.isSendingMessage = false;
      },
      complete: () => {
        this.isSendingMessage = false;
      },
    });
  }

  private refreshActiveSessionSilently(): void {
    if (!this.activeSession) {
      return;
    }

    const activeSessionId = this.activeSession.id;

    this.searchService.getSearchById(activeSessionId).subscribe({
      next: (sessionWithHistory) => {
        this.activeSession = sessionWithHistory;
      },
    });
  }

  deleteSession(sessionId: string, event: MouseEvent): void {
    event.stopPropagation();

    const confirmed = confirm('Delete this search session?');

    if (!confirmed) {
      return;
    }

    this.deletingSessionId = sessionId;
    this.errorMessage = '';

    this.searchService.deleteSearch(sessionId).subscribe({
      next: () => {
        this.sessions = this.sessions.filter((session) => session.id !== sessionId);

        if (this.activeSession?.id === sessionId) {
          this.activeSession = null;
          this.messages = [];

          if (this.sessions.length > 0) {
            this.selectSession(this.sessions[0].id);
          }
        }
      },
      error: () => {
        this.errorMessage = 'Could not delete this search session.';
        this.deletingSessionId = null;
      },
      complete: () => {
        this.deletingSessionId = null;
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/']);
  }
}
