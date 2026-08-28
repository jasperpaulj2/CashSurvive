"""
Shared pytest fixtures.

Uses a separate in-memory SQLite database for tests so they never
touch the real cashsurvive.db file, and each test gets a clean slate.
"""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from data.database import Base, get_db
from data import models  # noqa: F401  (ensures models are registered on Base)
from main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture()
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_company(db_session):
    from data.repository import create_company
    from data.schemas import CompanyCreate

    return create_company(
        db_session,
        CompanyCreate(
            name="Test Co",
            currency="INR",
            current_cash=1_000_000,
            minimum_cash_reserve=300_000,
        ),
    )


TODAY = dt.date.today()
