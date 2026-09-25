import { CommonModule, CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  AdminService,

} from '../../../services/admin.service';
import { DailyUsage, SessionUsage, UsageSummary } from '../../../models/admin';

@Component({
  selector: 'app-admin-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule, CurrencyPipe, DecimalPipe],
  templateUrl: './admin-analytics.component.html',
  styleUrl: './admin-analytics.component.css',
})
export class AdminAnalyticsComponent implements OnInit {
  private readonly adminService = inject(AdminService);

  summary: UsageSummary | null = null;
  dailyUsage: DailyUsage[] = [];
  sessionUsage: SessionUsage[] = [];

  dateFrom = '';
  dateTo = '';

  sessionSkip = 0;
  sessionLimit = 20;
  sessionCount = 0;

  isLoading = false;
  errorMessage = '';

  ngOnInit(): void {
    this.loadAnalytics();
  }

  loadAnalytics(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.adminService.getUsageSummary(this.dateFrom, this.dateTo).subscribe({
      next: (summary) => {
        this.summary = summary;
      },
      error: () => {
        this.errorMessage = 'Could not load usage summary.';
      },
    });

    this.adminService.getDailyUsage(this.dateFrom, this.dateTo).subscribe({
      next: (daily) => {
        this.dailyUsage = daily;
      },
      error: () => {
        this.errorMessage = 'Could not load daily usage.';
      },
    });

    this.adminService
      .getSessionUsage(this.sessionSkip, this.sessionLimit)
      .subscribe({
        next: (response) => {
          this.sessionUsage = response.data;
          this.sessionCount = response.count;
          this.isLoading = false;
        },
        error: () => {
          this.errorMessage = 'Could not load session usage.';
          this.isLoading = false;
        },
      });
  }

  applyDateFilter(): void {
    this.loadAnalytics();
  }

  clearDateFilter(): void {
    this.dateFrom = '';
    this.dateTo = '';
    this.loadAnalytics();
  }

  nextSessionPage(): void {
    if (this.sessionSkip + this.sessionLimit >= this.sessionCount) {
      return;
    }

    this.sessionSkip += this.sessionLimit;
    this.loadAnalytics();
  }

  previousSessionPage(): void {
    if (this.sessionSkip === 0) {
      return;
    }

    this.sessionSkip = Math.max(0, this.sessionSkip - this.sessionLimit);
    this.loadAnalytics();
  }
}