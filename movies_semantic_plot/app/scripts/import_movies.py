import logging
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select

from app.db import get_database, get_db
from app.models.movie import Movie
from app.models.genre import Genre


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "movies_plots.csv"
# DATASET_PATH = ""


def clean_optional_string(value) -> str | None:
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def clean_optional_int(value) -> int | None:
    if pd.isna(value):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def split_genres(value) -> list[str]:
    if pd.isna(value):
        return []

    return [
        genre.strip()
        for genre in str(value).split("|")
        if genre.strip()
    ]


def get_or_create_genre(
    session: Session,
    name: str,
    genre_cache: dict[str, Genre],
) -> Genre:
    if name in genre_cache:
        return genre_cache[name]

    genre = session.exec(
        select(Genre).where(Genre.name == name)
    ).first()

    if genre is not None:
        genre_cache[name] = genre
        return genre

    genre = Genre(name=name)

    session.add(genre)
    session.commit()
    session.refresh(genre)
    print(f"imported genre: {genre.name}, id: {genre.id}", )

    genre_cache[name] = genre

    return genre


def movie_exists(
    session: Session,
    title: str,
    year: int | None,
) -> bool:
    statement = select(Movie).where(Movie.title == title)

    if year is not None:
        statement = statement.where(Movie.year == year)
    else:
        statement = statement.where(Movie.year.is_(None))

    existing_movie = session.exec(statement).first()

    return existing_movie is not None


def import_movies(csv_path: Path, engine) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)

    genre_cache: dict[str, Genre] = {}

    imported_count = 0
    skipped_count = 0

    with Session(engine) as session:
        for _, row in df.iterrows():
            title = clean_optional_string(row.get("Title"))

            if title is None:
                skipped_count += 1
                continue

            year = clean_optional_int(row.get("Year"))

            if movie_exists(session=session, title=title, year=year):
                skipped_count += 1
                continue

            genre_names = split_genres(row.get("Genres"))

            genres = [
                get_or_create_genre(
                    session=session,
                    name=genre_name,
                    genre_cache=genre_cache,
                )
                for genre_name in genre_names
            ]
            movie_id = clean_optional_int(row.get("MovieID"))

            movie = Movie(
                id = movie_id,
                title=title,
                year=year,
                director=clean_optional_string(row.get("Director")),
                cast=clean_optional_string(row.get("Cast")),
                plot=clean_optional_string(row.get("Plot")),
                genres=genres,
            )

            session.add(movie)

            imported_count += 1

            if imported_count % 500 == 0:
                session.commit()
                logger.info("Imported %s movies...", imported_count)

        session.commit()

    logger.info("Movie import completed")
    logger.info("Imported movies: %s", imported_count)
    logger.info("Skipped movies: %s", skipped_count)


def main() -> None:
    db = get_database()
    db.create_db_and_tables()
    engine = db.engine
    s = get_db()
    
    
    import_movies(DATASET_PATH,engine)


if __name__ == "__main__":
    main()



# def main() -> None:
#     db = get_database('sqlite')
#     db.create_db_and_tables()
#     eng = db.engine


# python -m app.scripts.import_movies
# docker compose --profile tools run --rm import_movies















# import logging
# from pathlib import Path

# import pandas as pd
# from sqlmodel import Session, select, text

# from app.db import get_database
# from app.models.movie import Movie
# from app.models.genre import Genre
# from app.models.many_many_links import MovieGenreLink   


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# DATASET_PATH = PROJECT_ROOT / "data" / "movies_plots.csv"


# def clean_optional_string(value) -> str | None:
#     if pd.isna(value):
#         return None
#     value = str(value).strip()
#     return value if value else None


# def split_genres(value) -> list[str]:
#     if pd.isna(value):
#         return []
#     return [g.strip() for g in str(value).split("|") if g.strip()]


# def get_or_create_genre(session: Session, name: str, genre_cache: dict[str, Genre]) -> Genre:
#     """Βρίσκει ή δημιουργεί ένα Genre (ίδιο με το αρχικό script)."""
#     if name in genre_cache:
#         return genre_cache[name]

#     genre = session.exec(select(Genre).where(Genre.name == name)).first()
#     if genre is None:
#         genre = Genre(name=name)
#         session.add(genre)
#         session.commit()
#         session.refresh(genre)
#         logger.info(f"Δημιουργήθηκε genre: {genre.name} (id={genre.id})")
#     genre_cache[name] = genre
#     return genre


# def restore_movie_genre_links(csv_path: Path, engine) -> None:
#     if not csv_path.exists():
#         raise FileNotFoundError(f"Το αρχείο δεν βρέθηκε: {csv_path}")

#     df = pd.read_csv(csv_path)

#     with Session(engine) as session:
#         # 1. Καθαρίζουμε όλες τις υπάρχουσες συνδέσεις (γιατί έχουν παλιά genre_id)
#         logger.info("Διαγραφή όλων των εγγραφών από τον πίνακα σύνδεσης...")
#         session.execute(text("DELETE FROM movie_genre_link"))   # ή το σωστό όνομα πίνακα
#         session.commit()

#         genre_cache: dict[str, Genre] = {}
#         processed = 0
#         linked = 0
#         skipped = 0

#         for _, row in df.iterrows():
#             movie_id = row.get("MovieID")
#             if pd.isna(movie_id):
#                 skipped += 1
#                 continue

#             # Βρίσκουμε την ταινία με βάση το ID της (ή με title+year αν προτιμάς)
#             movie = session.get(Movie, int(movie_id))
#             if movie is None:
#                 skipped += 1
#                 continue

#             genre_names = split_genres(row.get("Genres"))
#             if not genre_names:
#                 skipped += 1
#                 continue

#             # Παίρνουμε ή δημιουργούμε τα Genre
#             genres = [
#                 get_or_create_genre(session, name, genre_cache)
#                 for name in genre_names
#             ]

#             # Αντικαθιστούμε τις σχέσεις της ταινίας (θα διαγράψει τις παλιές και θα βάλει τις νέες)
#             movie.genres = genres
#             session.add(movie)

#             linked += 1
#             processed += 1

#             if processed % 500 == 0:
#                 session.commit()
#                 logger.info(f"Επεξεργάστηκαν {processed} ταινίες, συνδέθηκαν {linked}...")

#         # Τελικό commit
#         session.commit()
#         logger.info(f"Ολοκληρώθηκε! Συνδέθηκαν {linked} ταινίες, παραλείφθηκαν {skipped}.")


# def main():
#     db = get_database()
#     db.create_db_and_tables()   # σιγουρεύουμε ότι οι πίνακες υπάρχουν
#     engine = db.engine

#     restore_movie_genre_links(DATASET_PATH, engine)


# if __name__ == "__main__":
#     main()