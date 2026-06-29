# Database — Migrations & Data Port

Everything about getting your existing data into Postgres.

## Two separate concerns

1. **Schema migrations** → Alembic (lives in `backend/`, configured here)
2. **One-time data port** → `migrate_sqlite_to_postgres.py` (moves your 44 funds + ~850 transactions)

---

## Phase 1 — Schema with Alembic

Alembic is **already wired** in `backend/`:
- `alembic.ini` — config (script location, logging)
- `alembic/env.py` — async-aware, reads `settings.DATABASE_URL` + `app.database.Base.metadata`
- `alembic/versions/0001_initial.py` — the initial 4-table schema (hand-written
  to mirror the desktop SQLite DB exactly)

So you do **not** need `alembic init`. From `backend/`:
```powershell
# Apply the schema to Postgres
alembic upgrade head

# Later, after changing a model, generate a new migration:
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

This creates the 4 tables in Postgres: `funds`, `transactions`,
`expense_categories`, `bpi_balance`.

> The models use a metadata **naming convention** (`pk_`, `uq_`, `fk_`, `ix_`)
> so `--autogenerate` produces stable, churn-free diffs that match
> `0001_initial.py`.

---

## Phase 1 (cont.) — Port existing data

The desktop app's data lives in `../../budget_tracker.db` (SQLite).
Run the port script **once** after the schema exists:

```powershell
cd database
python migrate_sqlite_to_postgres.py
```

It:
1. Reads every row from the old SQLite DB
2. Inserts them into Postgres in FK-safe order (funds → transactions, etc.)
3. Verifies row counts match
4. Prints a summary

> ⚠ Idempotency: the script truncates the Postgres tables first, so it's safe
> to re-run. Comment out the truncate block if you want append-only behavior.

---

## Verifying the port

After running, check parity:
```powershell
# Old (SQLite)
python -c "import sqlite3; c=sqlite3.connect('../../budget_tracker.db'); print('funds', c.execute('SELECT COUNT(*) FROM funds').fetchone()[0]); print('txns', c.execute('SELECT COUNT(*) FROM transactions').fetchone()[0])"
```
The script prints the new Postgres counts — they must match.
