"""app/database.py — async SQLAlchemy engine + session factory.

The engine and session factory are created **lazily** (on first use) rather than
at import time. This keeps `from app.database import Base` cheap and side-effect
free, so tooling that only needs the metadata — Alembic's env.py, unit tests,
`--autogenerate` — can import models without the async driver (asyncpg) being
installed or a live DATABASE_URL being reachable.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Deterministic constraint/index names so Alembic `--autogenerate` produces
# stable, churn-free diffs (the hand-written 0001_initial migration uses these
# exact names: pk_<table>, uq_<table>_<col>, fk_<table>_<col>_<ref>, ix_…).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Create (once) and return the async engine.

    Lazy so importing this module never forces asyncpg to load.
    """
    return create_async_engine(settings.DATABASE_URL, echo=False, future=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Create (once) and return the async session factory."""
    return async_sessionmaker(
        bind=get_engine(), class_=AsyncSession, expire_on_commit=False
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with get_sessionmaker()() as session:
        yield session
