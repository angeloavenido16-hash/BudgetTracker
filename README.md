# Budget Tracker

A personal finance tracking app. Backend in FastAPI, frontend in React.

| Layer | Stack |
|-------|-------|
| **Backend** | FastAPI + SQLAlchemy 2.0 + SQLite (dev) / asyncpg (prod) + Alembic |
| **Frontend** | React 18 + Vite + TypeScript + TanStack Table + Recharts |
| **Auth** | JWT (single user) |
| **Hosting** | Railway + Docker + PostgreSQL |

## Structure

```
├── backend/         FastAPI app (API + business logic)
├── frontend/        React + Vite SPA
├── database/        SQLite → Postgres data migration script
├── deployment/      Docker Compose, nginx config
└── docs/            Formula spec, API contract, parity checklist
```

## Quick start

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload          # → http://localhost:8000/docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                             # → http://localhost:5173
```

For Docker Compose (Postgres + backend + frontend):

```bash
docker compose -f deployment/docker-compose.yml up --build
```

## Migrating data from the desktop app

If you have existing data from the original desktop SQLite app:

1. Copy `budget_tracker.db` to the repo root
2. Run Alembic migrations: `cd backend && alembic upgrade head`
3. Run the migration script: `cd database && python migrate_sqlite_to_postgres.py`

## Deployment (Railway)

Two Railway services, both using Dockerfiles at their root:

**Backend service** — `backend/Dockerfile` + `backend/railway.json`
- Attach a PostgreSQL plugin
- Set env vars in Railway dashboard:
  - `JWT_SECRET` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
  - `APP_USERNAME` / `APP_PASSWORD`
  - `FRONTEND_ORIGINS` (comma-separated frontend URLs)

**Frontend service** — `frontend/Dockerfile` + `frontend/railway.json`
- Build arg `VITE_API_URL` must be set to the backend service URL
- Set in Railway: `RAILWAY_BUILD_ARGS = {"VITE_API_URL": "https://backend.up.railway.app"}`

## Docs

- [Formula spec](./docs/FORMULAS.md)
- [API contract](./docs/API_CONTRACT.md)
- [Parity checklist](./docs/PARITY_CHECKLIST.md)
