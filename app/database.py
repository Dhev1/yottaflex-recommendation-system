from sqlalchemy import create_engine, text

from app.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def check_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar() == 1