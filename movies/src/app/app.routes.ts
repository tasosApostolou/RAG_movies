import { Routes } from '@angular/router';

import { HomeComponent } from './pages/home/home.component';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { SearchComponent } from './pages/search/search.component';

import { UserLayoutComponent } from './pages/user/user-layout/user-layout.component';
import { UserMoviesComponent } from './pages/user/user-movies/user-movies.component';
import { UserRecommendationsComponent } from './pages/user/user-recommendations/user-recommendations.component';
import { UserFavoritesComponent } from './pages/user/user-favorites/user-favorites.component';

import { AdminLayoutComponent } from './pages/admin/admin-layout/admin-layout.component';
import { AdminDashboardComponent } from './pages/admin/admin-dashboard/admin-dashboard.component';
import { AdminMoviesComponent } from './pages/admin/admin-movies/admin-movies.component';
import { AdminMovieCreateComponent } from './pages/admin/admin-movie-create/admin-movie-create.component';
import { AdminAnalyticsComponent } from './pages/admin/admin-analytics/admin-analytics.component';

import { authGuard } from './guards/auth.guard';
import { adminGuard } from './guards/admin.guard';

export const routes: Routes = [
  {
    path: '',
    component: HomeComponent,
  },
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'register',
    component: RegisterComponent,
  },

  {
    path: 'user',
    component: UserLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'movies',
        pathMatch: 'full',
      },
      {
        path: 'movies',
        component: UserMoviesComponent,
      },
      {
        path: 'ask-ai',
        component: SearchComponent,
      },
      {
        path: 'recommendations',
        component: UserRecommendationsComponent,
      },
      {
        path: 'favorites',
        component: UserFavoritesComponent,
      },
    ],
  },

  {
    path: 'search',
    redirectTo: 'user/ask-ai',
  },

  {
    path: 'admin',
    component: AdminLayoutComponent,
    canActivate: [adminGuard],
    children: [
      {
        path: '',
        component: AdminDashboardComponent,
      },
      {
        path: 'movies',
        component: AdminMoviesComponent,
      },
      {
        path: 'movies/new',
        component: AdminMovieCreateComponent,
      },
      {
        path: 'analytics',
        component: AdminAnalyticsComponent,
      },
    ],
  },

  {
    path: '**',
    redirectTo: '',
  },
];
