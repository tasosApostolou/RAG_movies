import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select

from app.db import get_database
from app.models.movie import Movie
from app.models.rater import Rater
from app.models.ratings import Movie_Rating


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "movie_ratings.csv"


def clean_required_int(value) -> int | None:
    if pd.isna(value):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_required_stars(value) -> Decimal | None:
    if pd.isna(value):
        return None

    try:
        stars = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if stars < Decimal("0") or stars > Decimal("5"):
        return None

    return stars


def get_existing_movie_ids(session: Session) -> set[int]:
    movie_ids = session.exec(select(Movie.id)).all()
    return {movie_id for movie_id in movie_ids if movie_id is not None}


def get_existing_rater_ids(session: Session) -> set[int]:
    rater_ids = session.exec(select(Rater.id)).all()
    return {rater_id for rater_id in rater_ids if rater_id is not None}


def get_existing_movie_rating_pairs(session: Session) -> set[tuple[int, int]]:
    rows = session.exec(
        select(Movie_Rating.rater_id, Movie_Rating.movie_id)
    ).all()

    return {
        (rater_id, movie_id)
        for rater_id, movie_id in rows
    }


def import_dataset_raters(
    session: Session,
    rater_ids: set[int],
) -> int:
    existing_rater_ids = get_existing_rater_ids(session)

    imported_count = 0

    for rater_id in sorted(rater_ids):
        if rater_id in existing_rater_ids:
            continue

        rater = Rater(
            id=rater_id,
            user_id=None,
        )

        session.add(rater)
        imported_count += 1

        if imported_count % 1000 == 0:
            session.commit()
            logger.info("Imported %s raters...", imported_count)

    session.commit()

    return imported_count

def import_movie_ratings(csv_path: Path, engine) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_columns = {"RaterID", "MovieID", "Rating"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing columns from ratings CSV: {missing_columns}")

    imported_count = 0
    skipped_count = 0
    missing_movie_count = 0
    duplicate_count = 0

    with Session(engine) as session:
        existing_movie_ids = get_existing_movie_ids(session)

        unique_rater_ids: set[int] = set()

        for value in df["RaterID"]:
            rater_id = clean_required_int(value)

            if rater_id is not None:
                unique_rater_ids.add(rater_id)

        
        imported_raters = import_dataset_raters(
            session=session,
            rater_ids=unique_rater_ids,
        )
        

        logger.info("Imported raters: %s", imported_raters)

        existing_movie_rating_pairs = get_existing_movie_rating_pairs(session)

        for _, row in df.iterrows():
            rater_id = clean_required_int(row.get("RaterID"))
            movie_id = clean_required_int(row.get("MovieID"))
            stars_value = clean_required_stars(row.get("Rating"))

            if rater_id is None or movie_id is None or stars_value is None:
                skipped_count += 1
                continue

            if movie_id not in existing_movie_ids:
                missing_movie_count += 1
                skipped_count += 1
                continue

            movie_rating_pair = (rater_id, movie_id)

            if movie_rating_pair in existing_movie_rating_pairs:
                duplicate_count += 1
                skipped_count += 1
                continue

            movie_rating = Movie_Rating(
                rater_id=rater_id,
                movie_id=movie_id,
                stars=stars_value,
            )

            session.add(movie_rating)
            existing_movie_rating_pairs.add(movie_rating_pair)

            imported_count += 1

            if imported_count % 1000 == 0:
                session.commit()
                logger.info("Imported %s movie ratings...", imported_count)

        session.commit()

    logger.info("Movie rating import completed")
    logger.info("Imported movie ratings: %s", imported_count)
    logger.info("Skipped movie ratings: %s", skipped_count)
    logger.info("Skipped because movie_id not found: %s", missing_movie_count)
    logger.info("Skipped duplicates: %s", duplicate_count)


def main() -> None:
    db = get_database("mysql")
    db.create_db_and_tables()

    engine = db.engine

    import_movie_ratings(DATASET_PATH, engine)


if __name__ == "__main__":
    main()


# Τρέξιμο:
# python -m app.scripts.import_ratings