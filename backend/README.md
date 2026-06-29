# Backend — FastAPI + SQLAlchemy 2.0

Async REST API that replaces the desktop app's `database.py`.

## Stack
- **FastAPI** — routing, validation, auto OpenAPI docs at `/docs`
- **SQLAlchemy 2.0** (async) + **asyncpg** — Postgres driver
- **Alembic** — schema migrations
- **Pydantic v2** — request/response schemas
- **python-jose** + **passlib** — JWT auth

## Folder layout
```
backend/
├── README.md
├── requirements.txt
├── .env.example
├── alembic.ini                  # ✅ Phase 1 — Alembic config
├── alembic/                     # ✅ Phase 1 — migration environment
│   ├── env.py                   #    async-aware, wired to app metadata
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py      #    initial 4-table schema
└── app/
    ├── main.py                  # FastAPI entrypoint (routers wired)
    ├── config.py                # settings (env vars)
    ├── database.py              # async engine + session (lazy)
    ├── security.py              # ✅ Phase 2 — JWT + single-user auth
    ├── models/                  # SQLAlchemy ORM models
    │   ├── fund.py
    │   ├── transaction.py
    │   ├── category.py
    │   └── bpi_balance.py
    ├── schemas/                 # ✅ Phase 2 — Pydantic request/response models
    │   ├── auth.py  fund.py  transaction.py  category.py
    │   └── bpi.py   dashboard.py  reports.py
    ├── routers/                 # ✅ Phase 2 — API endpoints
    │   ├── auth.py  funds.py  transactions.py  categories.py
    │   └── bpi.py   dashboard.py  reports.py
    └── services/
        ├── summaries.py         # ⭐ ALL financial formulas (parity-locked)
        └── queries.py           # ✅ Phase 2 — async fetch helpers → dict rows
```

> Tests: `tests/test_formula_parity.py` (13 formula tests) +
> `tests/test_api_endpoints.py` (full end-to-end API run on in-memory SQLite).
> Run `pytest` from `backend/`.

## Setup (Phase 1)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # then edit DATABASE_URL, JWT_SECRET

# Start Postgres (from deployment/):  docker compose -f ../deployment/docker-compose.yml up -d db
# Then create the schema:
alembic upgrade head
```

## Run
```powershell
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## API surface (maps 1:1 from desktop `database.py`)

| Desktop function | HTTP endpoint |
|---|---|
| `get_funds()` | `GET /funds` |
| `get_fund_by_id()` | `GET /funds/{id}` |
| `add_fund()` | `POST /funds` |
| `update_fund()` | `PUT /funds/{id}` |
| `delete_fund()` | `DELETE /funds/{id}` |
| `get_transactions()` | `GET /funds/{id}/transactions` |
| `add_transaction()` | `POST /transactions` |
| `update_transaction()` | `PUT /transactions/{id}` |
| `delete_transaction()` | `DELETE /transactions/{id}` |
| `get_categories()` | `GET /categories` |
| `add_category()` | `POST /categories` |
| `delete_category()` | `DELETE /categories/{name}` |
| `get_fund_summary()` | `GET /funds/{id}/summary` |
| `get_all_fund_summaries()` | `GET /funds/summaries` |
| `get_dashboard_totals()` | `GET /dashboard/totals` |
| `get_expense_by_category()` | `GET /reports/by-category` |
| `get_spending_over_time()` | `GET /reports/over-time` |
| `get_latest_bpi_balance()` | `GET /settings/bpi` |
| `update_bpi_balance()` | `PUT /settings/bpi` |
| Excel import | `POST /settings/import` (multipart upload) |

> ⭐ The formulas in `app/services/summaries.py` are already ported from the
> desktop app. **Do not change the math** — verify parity instead
> (see `../docs/PARITY_CHECKLIST.md`).
