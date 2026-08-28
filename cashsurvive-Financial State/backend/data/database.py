"""
Database engine, session factory, and declarative base.

Uses SQLite for the hackathon prototype. The engine is created from a
single DATABASE_URL constant so swapping to PostgreSQL later only
requires changing that one string (e.g. "postgresql+psycopg://...")
and adding the appropriate driver to requirements.txt.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./cashsurvive.db"

# check_same_thread=False is only needed for SQLite when the same
# connection may be used across FastAPI's threaded request handling.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


def init_db() -> None:
    """Create all tables. Safe to call multiple times (no-op if tables exist)."""
    # Import models here so they are registered on Base.metadata before
    # create_all runs, without creating a circular import at module load time.
    from data import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
