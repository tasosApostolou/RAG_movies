import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MovieService } from '../../../services/movie.service';
import { MoviePublic } from '../../../models/movie';

@Component({
  selector: 'app-user-favorites',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-favorites.component.html',
  styleUrl: './user-favorites.component.css',
})
export class UserFavoritesComponent implements OnInit {
  private readonly movieService = inject(MovieService);

  favorites: MoviePublic[] = [];
  count = 0;

  skip = 0;
  limit = 20;
  q = '';

  isLoading = false;
  errorMessage = '';
  successMessage = '';

  selectedMovieForPlot: MoviePublic | null = null;
  removingMovieId: number | null = null;

  ngOnInit(): void {
    this.loadFavorites();
  }

  loadFavorites(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.movieService.getFavorites(this.skip, this.limit, this.q).subscribe({
      next: (response) => {
        this.favorites = response.movies;
        this.count = response.count;
      },
      error: () => {
        this.errorMessage = 'Could not load favorite movies.';
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      },
    });
  }

  search(): void {
    this.skip = 0;
    this.loadFavorites();
  }

  nextPage(): void {
    if (this.skip + this.limit >= this.count) {
      return;
    }

    this.skip += this.limit;
    this.loadFavorites();
  }

  previousPage(): void {
    if (this.skip === 0) {
      return;
    }

    this.skip = Math.max(0, this.skip - this.limit);
    this.loadFavorites();
  }

  openPlot(movie: MoviePublic): void {
    this.selectedMovieForPlot = movie;
  }

  closePlot(): void {
    this.selectedMovieForPlot = null;
  }

  removeFromFavorites(movie: MoviePublic): void {
    const confirmed = confirm(`Remove "${movie.title}" from favorites?`);

    if (!confirmed) {
      return;
    }

    this.removingMovieId = movie.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.movieService.removeFromFavorites(movie.id).subscribe({
      next: () => {
        this.favorites = this.favorites.filter((item) => item.id !== movie.id);
        this.count = Math.max(0, this.count - 1);
        this.successMessage = `"${movie.title}" was removed from favorites.`;

        if (this.selectedMovieForPlot?.id === movie.id) {
          this.selectedMovieForPlot = null;
        }
      },
      error: () => {
        this.errorMessage = 'Could not remove movie from favorites.';
        this.removingMovieId = null;
      },
      complete: () => {
        this.removingMovieId = null;
      },
    });
  }

  getGenres(movie: MoviePublic): string {
    return movie.genres.map((genre) => genre.name).join(', ');
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