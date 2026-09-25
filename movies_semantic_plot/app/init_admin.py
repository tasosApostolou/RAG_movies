import logging

from sqlmodel import Session, select

from app.core.config import settings
# from app.db import create_db_and_tables, engine
from app.db import get_database, get_db
from app.security import hash_password
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(session: Session) -> None:
    """
    Creates initial application data.

    Currently:
    - first superuser/admin

    This function is idempotent:
    running it many times will not create duplicate admin users.
    """

    existing_user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()

    if existing_user:
        logger.warn("Superuser already exists: %s", settings.FIRST_SUPERUSER)
        return

    user = User(
        email=settings.FIRST_SUPERUSER,
        hashed_password=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
        full_name="Admin",
        is_active=True,
        is_superuser=True,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info("Superuser created: %s", user.email)


def init() -> None:
    # db = get_database("mysql")
    db = get_db()
    db.create_db_and_tables()

    with Session(db.engine) as session:
        init_db(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()


# python -m app.init_admin