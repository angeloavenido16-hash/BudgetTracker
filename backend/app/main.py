"""
app/main.py — FastAPI entrypoint.

Phase 2: all routers are wired below. The financial math lives in
app/services/summaries.py (parity-locked against the desktop app).
Run:  uvicorn app.main:app --reload   →  http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import get_sessionmaker
from app.models import User
from app.routers import (
    auth,
    bpi,
    categories,
    dashboard,
    funds,
    reports,
    transactions,
)
from app.security import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed a default admin only when the users table is empty."""
    async with get_sessionmaker()() as session:
        try:
            any_user = await session.scalar(select(User).limit(1))
            if any_user is None:
                import logging
                logging.warning(
                    "No users found — creating seed admin "
                    "('%s' / '%s'). Change the password immediately.",
                    settings.SEED_USERNAME, settings.SEED_PASSWORD,
                )
                session.add(
                    User(
                        username=settings.SEED_USERNAME,
                        password_hash=hash_password(settings.SEED_PASSWORD),
                    )
                )
                await session.commit()
            else:
                # Keep user #1's password in sync with SEED_PASSWORD
                # (safety net for migrations that insert a stale placeholder).
                user1 = await session.get(User, 1)
                if user1 is not None:
                    user1.password_hash = hash_password(settings.SEED_PASSWORD)
                    if not user1.is_admin:
                        user1.is_admin = True
                    await session.commit()
        except Exception:
            await session.rollback()
    yield


app = FastAPI(
    title="Budget Tracker API",
    version="1.0.0",
    description="Web migration of the desktop Budget Tracker app.",
    lifespan=lifespan,
)

# ── CORS (comma-separated origins from env) ──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.FRONTEND_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(funds.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(bpi.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
