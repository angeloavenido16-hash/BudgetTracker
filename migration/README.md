# 🚀 Budget Tracker — Web Migration

Migrating the **desktop** Budget Tracker (Python + customtkinter + SQLite)
to a **web app** with the following stack:

| Layer | Stack |
|-------|-------|
| **Backend** | FastAPI (Python) — async, Pydantic validation, auto OpenAPI docs |
| **ORM** | SQLAlchemy 2.0 + asyncpg + Alembic (migrations) |
| **Frontend** | React + Vite + TypeScript + TanStack Table + Recharts |
| **Auth** | Simple JWT (single user) |
| **Hosting** | Railway + Docker + PostgreSQL |

---

## 📁 Folder structure

```
migration/
├── README.md            ← you are here (master plan)
├── backend/             ← FastAPI app (API + business logic)
├── frontend/            ← React + Vite SPA
├── database/            ← Alembic migrations + SQLite→Postgres data port
├── deployment/          ← Docker, docker-compose, Railway config
└── docs/                ← formula spec, API contract, parity checklist
```

Each folder has its **own README** with detailed steps.

---

## 🧭 Where do we start? (recommended order)

The golden rule: **build the backend first, prove the formulas match the
desktop app, then build the UI on top of a known-correct API.**

### Phase 0 — Foundations  ✅ *scaffolded for you*
- [x] Create monorepo folder structure
- [x] Port color palette → `frontend/src/theme.ts`
- [x] Port summary + dashboard formulas → `backend/app/services/summaries.py`
- [x] Port dashboard-chart + **Reports statistics** formulas (overview, category
      stats, fund flows, spending-over-time, expense-by-category, years)
- [x] Document the formula rules → `docs/FORMULAS.md`
- [x] Lock all formulas with parity tests → `backend/tests/test_formula_parity.py`
- [x] Build the Reports page (3 tabs + Year/Month/Fund filters) →
      `frontend/src/pages/Reports.tsx` (+ `hooks/useReports.ts`)

### Phase 1 — Backend data layer  👈 **START HERE**
1. `cd migration/backend`
2. Create a virtualenv & `pip install -r requirements.txt`
3. Spin up Postgres locally (see `deployment/README.md` → docker-compose)
4. Define the 4 SQLAlchemy models (`app/models/`)
5. `alembic upgrade head` to create tables
6. Run the **data migration** (`database/migrate_sqlite_to_postgres.py`)

### Phase 2 — Backend API
7. Pydantic schemas (`app/schemas/`)
8. Routers: funds, transactions, categories, dashboard, reports, settings, auth
9. **Verify formula parity** against the desktop app (`docs/PARITY_CHECKLIST.md`)
10. Open http://localhost:8000/docs — test every endpoint

### Phase 3 — Auth
11. JWT login (single user), protect all routes

### Phase 4 — Frontend
12. `cd migration/frontend && npm install && npm run dev`
13. API client + React Query
14. Pages in this order: Dashboard → Funds → Transactions → Reports → Settings
15. Rebuild custom widgets: CategoryPicker, CalendarPicker, masking toggle

### Phase 5 — Deploy
16. Dockerize backend + frontend  ✅ *assets in `deployment/`*
17. Push to Railway, attach Postgres plugin, set env vars

> **Status (current):** Phases 0–4 complete — backend, auth, and all five pages
> are built and running locally against the desktop SQLite DB, with formula
> parity verified. Deploy assets (`deployment/`) are scaffolded; Phase 5 push to
> Railway is the remaining step.

---

## ✅ What transfers from the desktop app (the valuable part)

- **All financial formulas** — already ported into `backend/app/services/summaries.py`
- **Category rules** — savings > 0, carry_over > 0, house (both signs), "other" fund logic
- **Dashboard charts** — spending-over-time + expense-by-category (positive-only,
  `txn_date`-based months, Year filter)
- **Reports statistics** — Overview / Category Stats / Ins & Outs, with the
  shared Year / Month / Fund filters (ported verbatim, parity-tested)
- **DB schema** — 4 tables (funds, transactions, expense_categories, bpi_balance)
- **Excel importer** — `importer.py` openpyxl logic reused server-side
- **Color theme** — ported to `frontend/src/theme.ts`

## ❌ What gets rebuilt (UI / runtime only)

- customtkinter widgets → React components
- matplotlib charts → Recharts
- Sync SQLite calls → async SQLAlchemy
- Event/refresh model → React Query cache invalidation

---

## 🔗 Quick links

- Backend setup → [`backend/README.md`](./backend/README.md)
- Frontend setup → [`frontend/README.md`](./frontend/README.md)
- Database / migrations → [`database/README.md`](./database/README.md)
- Deployment → [`deployment/README.md`](./deployment/README.md)
- Formula spec → [`docs/FORMULAS.md`](./docs/FORMULAS.md)
- Parity checklist → [`docs/PARITY_CHECKLIST.md`](./docs/PARITY_CHECKLIST.md)
