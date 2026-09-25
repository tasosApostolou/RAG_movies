import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AdminService } from '../../../services/admin.service';
import { MoviePublic } from '../../../models/movie';

@Component({
  selector: 'app-admin-movies',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePipe],
  templateUrl: './admin-movies.component.html',
  styleUrl: './admin-movies.component.css',
})
export class AdminMoviesComponent implements OnInit {
  private readonly adminService = inject(AdminService);

  movies: MoviePublic[] = [];
  count = 0;

  skip = 0;
  limit = 20;
  q = '';

  isLoading = false;
  errorMessage = '';

  selectedMovieForPlot: MoviePublic | null = null;
  deletingMovieId: number | null = null;

  ngOnInit(): void {
    this.loadMovies();
  }

  loadMovies(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.adminService.getMovies(this.skip, this.limit, this.q).subscribe({
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

  deleteMovie(movie: MoviePublic): void {
    const confirmed = confirm(`Delete "${movie.title}"?`);

    if (!confirmed) {
      return;
    }

    this.deletingMovieId = movie.id;
    this.errorMessage = '';

    this.adminService.deleteMovie(movie.id).subscribe({
      next: () => {
        this.movies = this.movies.filter((item) => item.id !== movie.id);
        this.count = Math.max(0, this.count - 1);

        if (this.selectedMovieForPlot?.id === movie.id) {
          this.selectedMovieForPlot = null;
        }
      },
      error: () => {
        this.errorMessage = 'Could not delete movie.';
        this.deletingMovieId = null;
      },
      complete: () => {
        this.deletingMovieId = null;
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