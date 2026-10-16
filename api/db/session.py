"""Database session factory and FastAPI dependency.

Why a module-level engine: SQLAlchemy engines are thread-safe and meant to be shared.
Creating one per request would be wasteful and exhaust connections quickly.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import settings

engine = create_engine(
    settings.database_url,
    # Pool size tuned for a single-process dev server.
    # Production deployments should set SQLALCHEMY_POOL_SIZE via config.
    pool_pre_ping=True,  # recycle stale connections automatically
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it when the request is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
