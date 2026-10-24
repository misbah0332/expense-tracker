from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import get_database_url


def create_db_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


def check_connection() -> None:
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()
