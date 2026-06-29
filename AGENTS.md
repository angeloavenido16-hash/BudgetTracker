# BudgetTracker — AGENTS.md

## Project structure

Two independent projects co-located at root:

| Directory | What | How to run |
|-----------|------|-----------|
| `backend/` | FastAPI + SQLAlchemy 2.0 + asyncpg | `uvicorn app.main:app --reload` |
| `frontend/` | React 18 + Vite + TypeScript | `npm run dev` (port 5173) |

Not a monorepo — no workspace tooling. Each is self-contained with its own config.

## Critical files

- `backend/app/services/summaries.py` — all financial formulas, parity-locked against the original desktop app. If you change formulas here, you MUST also confirm parity with `docs/FORMULAS.md`.
- `backend/app/database.py` — lazy async engine via `@lru_cache`. Don't import engine at module level (breaks Alembic and tests).
- `backend/app/config.py` — env-driven settings via pydantic-settings. Reads `.env` from backend root.
- `backend/app/security.py` — JWT single-user auth. bcrypt direct (not passlib). Password hashed once at import time.
- `frontend/src/api/client.ts` — axios instance with JWT interceptor. `VITE_API_URL` from `import.meta.env`.
- `frontend/src/theme.ts` — color palette ported from the original desktop app.

## Development

```bash
# Run backend (cd backend)
uvicorn app.main:app --reload

# Run backend tests (cd backend)
pytest                                # asyncio_mode=strict

# Run frontend dev server (cd frontend)
npm run dev

# Build frontend (cd frontend)
npm run build                         # tsc + vite build

# Lint frontend (cd frontend)
npm run lint                          # eslint src --ext ts,tsx

# Docker Compose (from repo root)
docker compose -f deployment/docker-compose.yml up --build
```

Always start backend before frontend during development.

## Alembic (cd backend)

```
alembic upgrade head
alembic revision --autogenerate -m "description"
```

Alembic's `env.py` imports `app.models` to register ORM models on `Base.metadata`. The naming convention (`pk_`, `uq_`, `fk_`, `ix_` prefixes) is set in `app/database.py` — keep it stable to avoid autogenerate churn.

## Deployment (Railway)

Two services, each with its own Dockerfile and railway.json:

- **Backend**: `backend/Dockerfile` + `backend/railway.json`. Attach Railway Postgres plugin. Set `JWT_SECRET`, `FRONTEND_ORIGINS`.
- **Frontend**: `frontend/Dockerfile` + `frontend/railway.json`. Build arg `VITE_API_URL` points to backend Railway URL.

JWT secret: `python -c "import secrets; print(secrets.token_hex(32))"`

## Important docs

- `docs/FORMULAS.md` — formula source of truth (required reading before touching summaries.py)
- `docs/API_CONTRACT.md` — endpoint-to-desktop-function mapping
- `docs/PARITY_CHECKLIST.md` — 75-item verification checklist

## Data migration

If migrating from the original desktop SQLite app:

1. Place `budget_tracker.db` at repo root
2. `cd backend && alembic upgrade head`
3. `cd database && python migrate_sqlite_to_postgres.py`
