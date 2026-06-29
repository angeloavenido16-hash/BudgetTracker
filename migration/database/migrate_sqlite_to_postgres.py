"""
migrate_sqlite_to_postgres.py
─────────────────────────────
One-time data port from the desktop app's SQLite DB into Postgres.

Run this ONCE, after the Alembic schema has been applied (`alembic upgrade head`).

    cd migration/database
    python migrate_sqlite_to_postgres.py

It is idempotent: it truncates the Postgres tables first, so re-running gives
the same result. Comment out `_truncate()` if you want append-only behaviour.

Reads connection info from ../backend/.env (DATABASE_URL).
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import psycopg2  # sync driver is simplest for a one-shot script
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# ── Paths ────────────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
SQLITE_PATH = HERE.parent.parent / "budget_tracker.db"   # the desktop app's DB
ENV_PATH = HERE.parent / "backend" / ".env"

# Fallback used when neither .env nor a DATABASE_URL env var is present.
# Matches the docker-compose Postgres service (budget/budget@localhost:5432).
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://budget:budget@localhost:5432/budget_tracker"
)

# Tables in FK-safe insertion order (parents first)
TABLES = ["expense_categories", "funds", "transactions", "bpi_balance"]

# Column lists must match both schemas exactly
COLUMNS = {
    "expense_categories": ["id", "name"],
    "funds": ["id", "name", "fund_type", "amount", "cutoff_date", "notes"],
    "transactions": [
        "id", "fund_id", "category", "amount", "txn_date", "remarks", "created_at",
    ],
    "bpi_balance": ["id", "balance", "recorded_at"],
}


# ── Connections ──────────────────────────────────────────────────────────────
def _pg_dsn() -> str:
    """Turn the async SQLAlchemy URL into a plain psycopg2 DSN.

    Resolution order:
      1. DATABASE_URL already in the environment (e.g. inside a container)
      2. DATABASE_URL from ../backend/.env
      3. DEFAULT_DATABASE_URL (docker-compose Postgres)
    """
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    url = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    # postgresql+asyncpg://user:pass@host:port/db  ->  postgresql://user:pass@host:port/db
    return url.replace("+asyncpg", "").replace("+psycopg2", "")


def _open_sqlite() -> sqlite3.Connection:
    if not SQLITE_PATH.exists():
        sys.exit(f"SQLite DB not found at {SQLITE_PATH}")
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Port logic ───────────────────────────────────────────────────────────────
def _truncate(pg_cur) -> None:
    """Wipe Postgres tables (children first) so the script is re-runnable."""
    for table in reversed(TABLES):
        pg_cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")


def _copy_table(sqlite_conn, pg_cur, table: str) -> int:
    cols = COLUMNS[table]
    col_csv = ", ".join(cols)
    rows = sqlite_conn.execute(f"SELECT {col_csv} FROM {table}").fetchall()
    if not rows:
        return 0
    values = [tuple(r[c] for c in cols) for r in rows]
    execute_values(
        pg_cur,
        f"INSERT INTO {table} ({col_csv}) VALUES %s",
        values,
    )
    return len(values)


def _fix_sequences(pg_cur) -> None:
    """After inserting explicit ids, bump each SERIAL sequence past MAX(id).

    Uses the 3-argument setval(seq, value, is_called) so the *empty-table* case
    is correct too: when a table has no rows we set the sequence to 1 with
    is_called=false, so the first inserted row still gets id=1 (the 2-arg form
    would set is_called=true and skip straight to id=2).
    """
    for table in TABLES:
        pg_cur.execute(
            f"SELECT setval("
            f"  pg_get_serial_sequence('{table}', 'id'),"
            f"  COALESCE((SELECT MAX(id) FROM {table}), 1),"
            f"  (SELECT MAX(id) IS NOT NULL FROM {table})"
            f")"
        )


def main() -> None:
    print(f"SQLite source : {SQLITE_PATH}")
    print(f"Postgres env  : {ENV_PATH}\n")

    sqlite_conn = _open_sqlite()
    pg_conn = psycopg2.connect(_pg_dsn())
    pg_conn.autocommit = False

    try:
        with pg_conn.cursor() as cur:
            print("Truncating Postgres tables…")
            _truncate(cur)

            counts: dict[str, int] = {}
            for table in TABLES:
                n = _copy_table(sqlite_conn, cur, table)
                counts[table] = n
                print(f"  {table:<20} {n:>6} rows")

            print("Fixing id sequences…")
            _fix_sequences(cur)
        pg_conn.commit()

        # ── Verify row counts match ──────────────────────────────────────────
        print("\nVerifying parity:")
        ok = True
        with pg_conn.cursor() as cur:
            for table in TABLES:
                src = sqlite_conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                dst = cur.fetchone()[0]
                flag = "✓" if src == dst else "✗ MISMATCH"
                if src != dst:
                    ok = False
                print(f"  {table:<20} sqlite={src:<6} postgres={dst:<6} {flag}")

        print("\n✅ Migration complete." if ok else "\n❌ Counts differ — review above.")
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
