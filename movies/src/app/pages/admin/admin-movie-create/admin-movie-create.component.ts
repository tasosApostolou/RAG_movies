import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AdminService } from '../../../services/admin.service';
import { MovieCreate } from '../../../models/movie';

interface GenreOption {
  id: number;
  name: string;
}

@Component({
  selector: 'app-admin-movie-create',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './admin-movie-create.component.html',
  styleUrl: './admin-movie-create.component.css',
})
export class AdminMovieCreateComponent {
  private readonly fb = inject(FormBuilder);
  private readonly adminService = inject(AdminService);
  private readonly router = inject(Router);

  isSubmitting = false;
  errorMessage = '';
  successMessage = '';

  genres: GenreOption[] = [
    { id: 1, name: 'Adventure' },
    { id: 2, name: 'Animation' },
    { id: 3, name: 'Children' },
    { id: 4, name: 'Comedy' },
    { id: 5, name: 'Fantasy' },
    { id: 6, name: 'Romance' },
    { id: 7, name: 'Drama' },
    { id: 8, name: 'Action' },
    { id: 9, name: 'Crime' },
    { id: 10, name: 'Thriller' },
    { id: 11, name: 'Horror' },
    { id: 12, name: 'Mystery' },
    { id: 13, name: 'Sci-Fi' },
    { id: 14, name: 'IMAX' },
    { id: 15, name: 'Documentary' },
    { id: 16, name: 'War' },
    { id: 17, name: 'Musical' },
    { id: 18, name: 'Film-Noir' },
    { id: 19, name: 'Western' },
  ];

  movieForm = this.fb.nonNullable.group({
    title: ['', [Validators.required, Validators.maxLength(255)]],
    year: [null as number | null],
    director: [''],
    plot: ['', [Validators.required]],
    poster_url: [''],
    imdb_id: [''],
    tmdb_id: [null as number | null],
    genre_ids: [[] as number[]],
  });

  isGenreSelected(genreId: number): boolean {
    return this.movieForm.controls.genre_ids.value.includes(genreId);
  }

  onGenreToggle(genreId: number, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const currentIds = this.movieForm.controls.genre_ids.value;

    if (checked) {
      this.movieForm.controls.genre_ids.setValue([...currentIds, genreId]);
      return;
    }

    this.movieForm.controls.genre_ids.setValue(
      currentIds.filter((id) => id !== genreId)
    );
  }

  onSubmit(): void {
    if (this.movieForm.invalid) {
      this.movieForm.markAllAsTouched();
      return;
    }

    const formValue = this.movieForm.getRawValue();

    const movie: MovieCreate = {
      title: formValue.title.trim(),
      year: formValue.year,
      director: formValue.director.trim() || null,
      plot: formValue.plot.trim(),
      poster_url: formValue.poster_url.trim() || null,
      imdb_id: formValue.imdb_id.trim() || null,
      tmdb_id: formValue.tmdb_id,
      genre_ids: formValue.genre_ids,
    };

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.adminService.createMovie(movie).subscribe({
      next: () => {
        this.successMessage = 'Movie created and ingested successfully.';
        this.movieForm.reset({
          title: '',
          year: null,
          director: '',
          plot: '',
          poster_url: '',
          imdb_id: '',
          tmdb_id: null,
          genre_ids: [],
        });
      },
      error: () => {
        this.errorMessage = 'Could not create movie or ingest it into ChromaDB.';
        this.isSubmitting = false;
      },
      complete: () => {
        this.isSubmitting = false;
      },
    });
  }

  goToMovies(): void {
    this.router.navigate(['/admin/movies']);
  }
}