"""Pytest fixtures for all tests.

DB isolation strategy: one engine and schema for the whole session; each test
function gets its own SAVEPOINT (begin_nested) which is rolled back at teardown.
This means every test starts with an empty database but schema creation only
happens once, keeping the suite fast.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.auth.hashing import hash_password
from api.config import settings
from api.db.models import Base, Role, User
from api.db.session import get_db
from api.main import app

# ---------------------------------------------------------------------------
# Engine pointed at the test database
# ---------------------------------------------------------------------------

test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# Session-scoped: create schema once, drop after the whole test run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables at the start of the test session, drop them at the end."""
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


# ---------------------------------------------------------------------------
# Function-scoped: isolate each test in a rolled-back transaction
# ---------------------------------------------------------------------------


@pytest.fixture()
def db():
    """Yield a Session whose changes are rolled back after each test.

    SAVEPOINT lets us run commits inside the test (so FastAPI route handlers
    that call db.commit() work normally) without persisting anything to disk.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    # Any nested commit becomes a SAVEPOINT release — still inside the outer
    # transaction which we roll back at the end.
    connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    """TestClient with the DB dependency overridden to use the test session."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reusable user fixtures
# ---------------------------------------------------------------------------


def _make_user(db, email: str, password: str, role: Role) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()  # get the id without committing
    return user


@pytest.fixture()
def viewer(db) -> User:
    return _make_user(db, "viewer@test.com", "viewerpass", Role.viewer)


@pytest.fixture()
def analyst(db) -> User:
    return _make_user(db, "analyst@test.com", "analystpass", Role.analyst)


@pytest.fixture()
def admin(db) -> User:
    return _make_user(db, "admin@test.com", "adminpass", Role.admin)


@pytest.fixture()
def inactive_user(db) -> User:
    user = User(
        email="inactive@test.com",
        hashed_password=hash_password("somepass"),
        role=Role.viewer,
        is_active=False,
    )
    db.add(user)
    db.flush()
    return user


# ---------------------------------------------------------------------------
# Helper: get a valid token for a given user via the API
# ---------------------------------------------------------------------------


def get_token(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
