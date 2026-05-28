from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def build_database_url() -> str:
    url = settings.DATABASE_URL or settings.POSTGRES_URI
    if url:
        if url.startswith("postgres://"):
            return "postgresql+psycopg2://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://"):
            return "postgresql+psycopg2://" + url.removeprefix("postgresql://")
        return url
    if settings.POSTGRES_HOST and settings.POSTGRES_DB and settings.POSTGRES_USER:
        password = settings.POSTGRES_PASSWORD or ""
        port = settings.POSTGRES_PORT or 5432
        ssl = f"?sslmode={settings.PGSSLMODE}" if settings.PGSSLMODE else ""
        return f"postgresql+psycopg2://{settings.POSTGRES_USER}:{password}@{settings.POSTGRES_HOST}:{port}/{settings.POSTGRES_DB}{ssl}"
    return "sqlite:///./ppl_hr.db"


class Base(DeclarativeBase):
    pass


engine = create_engine(build_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
