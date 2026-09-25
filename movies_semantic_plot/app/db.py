from sqlmodel import Session, SQLModel, create_engine
from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
 


# -------------------------------------------------------------------
# Base Database
# -------------------------------------------------------------------

class BaseDatabase:
    """BaseDatabase defines the database operations. It can be extended to support different database types (SQLite, Postgres, MySQL) by implementing the create_db_and_tables() and get_session() methods."""
    def __init__(
        self,
        url: str,
        echo: bool = False,
        connect_args: dict | None = None,
    ):
        self.engine = create_engine(
            url,
            echo=echo,
            connect_args=connect_args or {},
        )

    def create_db_and_tables(self):
        import app.models
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        with Session(self.engine) as session:
            yield session

# -------------------------------------------------------------------
# SQLite Database setup inheriting from BaseDatabase
# -------------------------------------------------------------------

class SQLiteDatabase(BaseDatabase):
    """SQLiteDatabase extends BaseDatabase to provide a concrete implementation for SQLite. It initializes the database connection with the appropriate URL and connection arguments for SQLite."""
    def __init__(
        self,
        path: str = "./movies.db",
        echo: bool = False,
    ):
        super().__init__(
            url=f"sqlite:///{path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )

# -------------------------------------------------------------------
# PostgreSQL Database
# -------------------------------------------------------------------

class PostgresDatabase(BaseDatabase):
    """
    PostgreSQL database implementation.
    """
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=movies_db
    def __init__(
        self,
        user: str = settings.POSTGRES_USER,
        password: str = settings.POSTGRES_PASSWORD,
        host: str = settings.POSTGRES_HOST,
        port: int = settings.POSTGRES_PORT,
        database: str = settings.POSTGRES_DB,
        echo: bool = False,
    ):
    
        super().__init__(
            url=(
                f"postgresql+psycopg://"
                f"{user}:{password}@{host}:{port}/{database}"
            ),
            echo=echo,
        )

# -------------------------------------------------------------------
# MySQL Database
# -------------------------------------------------------------------

class MySQLDatabase(BaseDatabase):
    """
    MySQL database implementation.
    """

    def __init__(
        self,
        user: str = settings.MYSQL_USER,
        password: str = settings.MYSQL_PASSWORD,
        host: str = settings.MYSQL_HOST,
        port: int = settings.MYSQL_PORT,
        database: str = settings.MYSQL_DB,
        echo: bool = False,
    ):
        super().__init__(
            url=(
                f"mysql+pymysql://"
                f"{user}:{password}@{host}:{port}/{database}"
            ),
            echo=echo,
        )


# -------------------------------------------------------------------
# Singleton db instance cache & Dependency SQLite by default
# -------------------------------------------------------------------

@lru_cache
def get_database(db_type:str = settings.DB_TYPE) -> BaseDatabase:
    """
    Returrn a singleton Database instance with default type of sqlite.
    this could be extended to return different database types based on config
    """
    match db_type:

        case "sqlite":
            sqlite_db = SQLiteDatabase( path="./movies.db", echo=False)
            return sqlite_db
        case "postgres":
            return PostgresDatabase()  # default config by class implementation

        case "mysql":
            return MySQLDatabase()  # default config by class implementation

        case _:
            raise ValueError(
                f"Unsupported database type: {db_type}"
            )

def get_mysql() -> BaseDatabase:
    return get_database("mysql")


def get_sqlite() -> BaseDatabase:
    return get_database("sqlite")

def get_postgress()-> BaseDatabase:
    return get_database("postgres")


def get_db() -> BaseDatabase:
    return get_database(settings.DB_TYPE)


# mysql_dep = Annotated[BaseDatabase,Depends(get_mysql)]

db_dep = Annotated[BaseDatabase,Depends(get_db)]

def get_session(db: db_dep):
    yield from db.get_session()












# from collections.abc import Generator

# from sqlmodel import Session, SQLModel, create_engine

# from app.core.config import settings

# engine = create_engine(
#     str(settings.SQLALCHEMY_DATABASE_URI),
#     echo=False,
# )


# def create_db_and_tables() -> None:
#     """
#     Creates database tables from SQLModel metadata.

#     Important:
#     All SQLModel table models must be imported before create_all,
#     otherwise SQLModel may not know that those tables exist.
#     """

#     # Import models so SQLModel registers them in metadata.
#     from app.models.user import User  # noqa: F401
#     from app.models.movie import Movie, Genre, MovieGenreLink, UserMovieFavorite  # noqa: F401

#     SQLModel.metadata.create_all(engine)


# def get_session() -> Generator[Session, None, None]:
#     with Session(engine) as session:
#         yield session