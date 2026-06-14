"""Engine e sessão SQLAlchemy 2.0."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from wealthlab_api.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos ORM."""


def _connect_args(url: str) -> dict:
    # SQLite + FastAPI: precisa liberar o uso da conexão entre threads.
    return {"check_same_thread": False} if url.startswith("sqlite") else {}


_settings = get_settings()
engine = create_engine(_settings.db_url, connect_args=_connect_args(_settings.db_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependency do FastAPI: abre e fecha uma sessão por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
