from sqlmodel import Session, select, func

from app.db import get_database
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.user import User


db = get_database("mysql")
# db = get_database("postgres")


def show_counts(session: Session) -> None:
    movie_count = session.exec(
        select(func.count(Movie.id))
    ).one()

    genre_count = session.exec(
        select(func.count(Genre.id))
    ).one()

    print("========== COUNTS ==========")
    print(f"Movies: {movie_count}")
    print(f"Genres: {genre_count}")
    print()


def show_first_movies(session: Session, limit: int = 10) -> None:
    movies = session.exec(
        select(Movie).limit(limit)
    ).all()

    print("========== FIRST MOVIES ==========")

    for movie in movies:
        genre_names = [genre.name for genre in movie.genres]

        print(f"{movie.id}. {movie.title} ({movie.year})")
        print(f"   Director: {movie.director}")
        print(f"   Genres: {genre_names}")
        print()

def show_users(session: Session, limit: int = 10) -> None:
    users = session.exec(
        select(User).limit(limit)
    ).all()

    print("========== FIRST USERS ==========")

    for user in users:
       print(f"\n\n{user.full_name} {user.id} {user.email} {user.is_active} {user.is_superuser}")
  


def show_genres(session: Session) -> None:
    # genres = session.exec(
    #     select(Genre).order_by(Genre.id)
    # ).all()
    genres = session.exec(
        select(Genre)
     ).all()


    print("========== GENRES ==========")

    for genre in genres:
        print(f"{genre.id}. {genre.name}")

    print()


def show_movies_by_genre(session: Session, genre_name: str, limit: int = 10) -> None:
    genre = session.exec(
        select(Genre).where(Genre.name == genre_name)
    ).first()

    if genre is None:
        print(f"Genre not found: {genre_name}")
        return

    print(f"========== MOVIES IN GENRE: {genre.name} ==========")

    for movie in genre.movies[:limit]:
        print(f"{movie.id}. {movie.title} ({movie.year})")

    print()


def main() -> None:
    with Session(db.engine) as session:
        show_users(session)
        show_counts(session)
        show_genres(session)
        show_first_movies(session, limit=10)
        show_movies_by_genre(session, genre_name="Comedy", limit=10)


if __name__ == "__main__":
    main()

 