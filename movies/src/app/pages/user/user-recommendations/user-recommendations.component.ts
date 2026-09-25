import { CommonModule, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';

import { MovieService } from '../../../services/movie.service';
import { RecommendedMoviePublic } from '../../../models/movie';

@Component({
  selector: 'app-user-recommendations',
  standalone: true,
  imports: [CommonModule, DecimalPipe],
  templateUrl: './user-recommendations.component.html',
  styleUrl: './user-recommendations.component.css',
})
export class UserRecommendationsComponent implements OnInit {
  private readonly movieService = inject(MovieService);

  recommendations: RecommendedMoviePublic[] = [];
  count = 0;

  skip = 0;
  limit = 20;

  isLoading = false;
  errorMessage = '';
  successMessage = '';

  selectedMovieForPlot: RecommendedMoviePublic | null = null;
  addingFavoriteMovieId: number | null = null;

  ngOnInit(): void {
    this.loadRecommendations();
  }

  loadRecommendations(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.movieService.getRecommendations(this.skip, this.limit).subscribe({
      next: (response) => {
        this.recommendations = response.movies;
        this.count = response.count;
      },
      error: () => {
        this.errorMessage = 'Could not load recommendations.';
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      },
    });
  }

  nextPage(): void {
    if (this.skip + this.limit >= this.count) {
      return;
    }

    this.skip += this.limit;
    this.loadRecommendations();
  }

  previousPage(): void {
    if (this.skip === 0) {
      return;
    }

    this.skip = Math.max(0, this.skip - this.limit);
    this.loadRecommendations();
  }

  openPlot(movie: RecommendedMoviePublic): void {
    this.selectedMovieForPlot = movie;
  }

  closePlot(): void {
    this.selectedMovieForPlot = null;
  }

  addToFavorites(movie: RecommendedMoviePublic): void {
    this.addingFavoriteMovieId = movie.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.movieService.addToFavorites(movie.id).subscribe({
      next: () => {
        this.successMessage = `"${movie.title}" was added to favorites.`;
      },
      error: () => {
        this.errorMessage = 'Could not add this movie to favorites.';
        this.addingFavoriteMovieId = null;
      },
      complete: () => {
        this.addingFavoriteMovieId = null;
      },
    });
  }

  get pageStart(): number {
    if (this.count === 0) {
      return 0;
    }

    return this.skip + 1;
  }

  get pageEnd(): number {
    return Math.min(this.skip + this.limit, this.count);
  }
}