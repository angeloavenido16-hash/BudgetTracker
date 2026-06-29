# Deployment

How to run the stack locally with Docker and ship it to Railway.

## Folder contents
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Local dev: Postgres + backend + frontend, one command |
| `Dockerfile.backend` | Production image for the FastAPI app |
| `Dockerfile.frontend` | Production image for the React build (served by nginx) |
| `nginx.conf` | SPA routing + reverse-proxy `/api` to backend |
| `railway.json` | Railway service config |

---

## Local development (Docker Compose)

From `migration/deployment/`:
```powershell
docker compose up --build
```
This starts:
- **db** — Postgres 16 on `localhost:5432`
- **backend** — FastAPI on `localhost:8000` (docs at `/docs`)
- **frontend** — React on `localhost:5173`

First run, apply the schema and port your existing data:
```powershell
# 1. Create the tables (runs inside the backend container)
docker compose exec backend alembic upgrade head

# 2. Port the 44 funds + ~850 transactions from the desktop SQLite DB.
#    Run this from the HOST (it reads ../../budget_tracker.db and reaches
#    Postgres via the exposed localhost:5432). The database/ folder and the
#    SQLite file are not mounted into the backend container.
cd ../database
python migrate_sqlite_to_postgres.py
```

Tear down (keep data): `docker compose down`
Tear down (wipe data): `docker compose down -v`

---

## Deploying to Railway

1. Push this repo to GitHub.
2. On Railway: **New Project → Deploy from GitHub repo**.
3. Add a **PostgreSQL** plugin → Railway injects `DATABASE_URL`.
   - Append `+asyncpg` so it becomes `postgresql+asyncpg://…`
4. Create two services from the same repo:
   - **backend** → root `migration/backend`, uses `Dockerfile.backend`
   - **frontend** → root `migration/frontend`, uses `Dockerfile.frontend`
5. Set backend env vars: `JWT_SECRET`, `APP_USERNAME`, `APP_PASSWORD`,
   `FRONTEND_ORIGIN` (the deployed frontend URL).
6. Set frontend build var: `VITE_API_URL` (the deployed backend URL).
7. Deploy. Run migrations once via Railway's shell:
   `alembic upgrade head` then the port script.

> 💡 Single-user app → the free/hobby tier is plenty.

---

## 🔐 Secrets & safety

- **Never commit `.env`** — the root `.gitignore` already excludes it (and all
  `*.db` files, so your real financial data never reaches GitHub). Commit
  `backend/.env.example` as the template instead.
- **Change the default login** before deploying. Set a strong `APP_USERNAME` /
  `APP_PASSWORD` and a random `JWT_SECRET` (e.g. `python -c "import secrets;
  print(secrets.token_urlsafe(48))"`).
- Set `FRONTEND_ORIGIN` to the exact deployed frontend URL so CORS stays locked.

---

## 🧹 Maintenance

- **Category cleanup** — `backend/scripts/clean_categories.py` normalizes
  category casing (title-case, acronym-aware), fixes mojibake, and merges
  case-duplicates. It backs up the DB first and is safe to re-run:
  ```powershell
  cd ../backend
  .venv\Scripts\python.exe scripts\clean_categories.py
  ```

