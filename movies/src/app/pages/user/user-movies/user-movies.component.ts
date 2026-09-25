import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MovieService } from '../../../services/movie.service';
import { MoviePublic } from '../../../models/movie';

@Component({
  selector: 'app-user-movies',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-movies.component.html',
  styleUrl: './user-movies.component.css',
})
export class UserMoviesComponent implements OnInit {
  private readonly movieService = inject(MovieService);

  movies: MoviePublic[] = [];
  count = 0;

  skip = 0;
  limit = 20;
  q = '';

  isLoading = false;
  errorMessage = '';
  successMessage = '';

  selectedMovieForPlot: MoviePublic | null = null;
  addingFavoriteMovieId: number | null = null;

  ngOnInit(): void {
    this.loadMovies();
  }

  loadMovies(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.movieService.getMovies(this.skip, this.limit, this.q).subscribe({
      next: (response) => {
        this.movies = response.movies;
        this.count = response.count;
      },
      error: () => {
        this.errorMessage = 'Could not load movies.';
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      },
    });
  }

  search(): void {
    this.skip = 0;
    this.loadMovies();
  }

  nextPage(): void {
    if (this.skip + this.limit >= this.count) {
      return;
    }

    this.skip += this.limit;
    this.loadMovies();
  }

  previousPage(): void {
    if (this.skip === 0) {
      return;
    }

    this.skip = Math.max(0, this.skip - this.limit);
    this.loadMovies();
  }

  openPlot(movie: MoviePublic): void {
    this.selectedMovieForPlot = movie;
  }

  closePlot(): void {
    this.selectedMovieForPlot = null;
  }

  addToFavorites(movie: MoviePublic): void {
    this.addingFavoriteMovieId = movie.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.movieService.addToFavorites(movie.id).subscribe({
      next: () => {
        this.successMessage = `"${movie.title}" was added to favorites.`;
      },
      error: () => {
        this.errorMessage =
          'Could not add this movie to favorites. The endpoint may not be implemented yet.';
        this.addingFavoriteMovieId = null;
      },
      complete: () => {
        this.addingFavoriteMovieId = null;
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