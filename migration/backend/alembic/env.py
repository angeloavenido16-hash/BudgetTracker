"""
Alembic migration environment — async-aware.

Wires Alembic to the app's own metadata and DATABASE_URL so that:
  * `alembic revision --autogenerate` diffs against app.models
  * `alembic upgrade head` runs through SQLAlchemy's async engine (asyncpg)

Run from `migration/backend/`:
    alembic upgrade head
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── App imports (prepend_sys_path=. in alembic.ini makes `app` importable) ───
from app.config import settings
from app.database import Base

# Import the models package so every model registers on Base.metadata.
# (Without this, --autogenerate would see an empty schema.)
import app.models  # noqa: F401

# ── Alembic Config object ────────────────────────────────────────────────────
config = context.config

# Inject the runtime DATABASE_URL from app settings (env-driven), overriding
# the placeholder in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from the alembic.ini [loggers] config.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support.
target_metadata = Base.metadata


# ── Offline mode (emit SQL without a DB connection) ──────────────────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL scripts only.

    No connection is made, so the async driver is irrelevant here; strip it so
    `alembic upgrade head --sql` renders DDL even without asyncpg installed.
    """
    url = config.get_main_option("sqlalchemy.url").replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connect + apply) ────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through it."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entrypoint for online migrations — drives the async runner."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
