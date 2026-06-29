"""
app/main.py — FastAPI entrypoint.

Phase 2: all routers are wired below. The financial math lives in
app/services/summaries.py (parity-locked against the desktop app).
Run:  uvicorn app.main:app --reload   →  http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    auth, bpi, categories, dashboard, funds, reports, transactions,
)

app = FastAPI(
    title="Budget Tracker API",
    version="1.0.0",
    description="Web migration of the desktop Budget Tracker app.",
)

# ── CORS (allow the Vite dev server + deployed frontend) ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
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
