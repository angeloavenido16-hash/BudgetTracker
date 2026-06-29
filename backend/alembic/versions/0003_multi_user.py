"""multi_user_support — add users table and user_id to all data tables.

Revision ID: 0003
Revises: 8d5a2c65d5e3

SQLite stores inline UNIQUE(name) constraints as auto-indexes without
user-facing names. Alembic's batch mode drop_constraint can't reference
them by name, so we use raw SQL table-recreation instead.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "8d5a2c65d5e3"


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # ── users table ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.execute(
        "INSERT INTO users (username, password_hash) "
        "VALUES ('admin', 'placeholder')"
    )

    # ── funds ────────────────────────────────────────────────────────────────
    # Remove UNIQUE(name), add user_id, add UNIQUE(user_id, name)
    op.execute("""
        CREATE TABLE funds_v2 (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1 REFERENCES users(id),
            name        TEXT    NOT NULL,
            fund_type   TEXT    NOT NULL DEFAULT 'salary',
            amount      REAL    NOT NULL DEFAULT 0,
            cutoff_date TEXT,
            notes       TEXT,
            UNIQUE(user_id, name)
        )
    """)
    op.execute(
        "INSERT INTO funds_v2 "
        "SELECT id, 1, name, fund_type, amount, cutoff_date, notes "
        "FROM funds"
    )
    op.execute("DROP TABLE funds")
    op.execute("ALTER TABLE funds_v2 RENAME TO funds")

    # ── expense_categories ───────────────────────────────────────────────────
    # Remove UNIQUE(name), add user_id, add UNIQUE(user_id, name)
    op.execute("""
        CREATE TABLE expense_categories_v2 (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL DEFAULT 1 REFERENCES users(id),
            name      TEXT    NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            UNIQUE(user_id, name)
        )
    """)
    op.execute(
        "INSERT INTO expense_categories_v2 "
        "SELECT id, 1, name, is_active "
        "FROM expense_categories"
    )
    op.execute("DROP TABLE expense_categories")
    op.execute("ALTER TABLE expense_categories_v2 RENAME TO expense_categories")

    # ── transactions ─────────────────────────────────────────────────────────
    # Add user_id
    op.execute("""
        CREATE TABLE transactions_v2 (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1 REFERENCES users(id),
            fund_id     INTEGER NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            txn_date    TEXT,
            remarks     TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    op.execute(
        "INSERT INTO transactions_v2 "
        "SELECT id, 1, fund_id, category, amount, txn_date, remarks, created_at "
        "FROM transactions"
    )
    op.execute("DROP TABLE transactions")
    op.execute("ALTER TABLE transactions_v2 RENAME TO transactions")

    # ── bpi_balance ──────────────────────────────────────────────────────────
    # Add user_id
    op.execute("""
        CREATE TABLE bpi_balance_v2 (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1 REFERENCES users(id),
            balance     REAL    NOT NULL,
            recorded_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    op.execute(
        "INSERT INTO bpi_balance_v2 "
        "SELECT id, 1, balance, recorded_at "
        "FROM bpi_balance"
    )
    op.execute("DROP TABLE bpi_balance")
    op.execute("ALTER TABLE bpi_balance_v2 RENAME TO bpi_balance")

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # Reverse bpi_balance
    op.execute("""
        CREATE TABLE bpi_balance_v2 (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            balance     REAL    NOT NULL,
            recorded_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    op.execute(
        "INSERT INTO bpi_balance_v2 "
        "SELECT id, balance, recorded_at FROM bpi_balance"
    )
    op.execute("DROP TABLE bpi_balance")
    op.execute("ALTER TABLE bpi_balance_v2 RENAME TO bpi_balance")

    # Reverse transactions
    op.execute("""
        CREATE TABLE transactions_v2 (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_id     INTEGER NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            txn_date    TEXT,
            remarks     TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    op.execute(
        "INSERT INTO transactions_v2 "
        "SELECT id, fund_id, category, amount, txn_date, remarks, created_at "
        "FROM transactions"
    )
    op.execute("DROP TABLE transactions")
    op.execute("ALTER TABLE transactions_v2 RENAME TO transactions")

    # Reverse expense_categories — preserve is_active, add back UNIQUE(name)
    op.execute("""
        CREATE TABLE expense_categories_v2 (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    op.execute(
        "INSERT INTO expense_categories_v2 "
        "SELECT id, name, is_active FROM expense_categories"
    )
    op.execute("DROP TABLE expense_categories")
    op.execute("ALTER TABLE expense_categories_v2 RENAME TO expense_categories")

    # Reverse funds — add back UNIQUE(name)
    op.execute("""
        CREATE TABLE funds_v2 (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL UNIQUE,
            fund_type     TEXT    NOT NULL DEFAULT 'salary',
            amount        REAL    NOT NULL DEFAULT 0,
            cutoff_date   TEXT,
            notes         TEXT
        )
    """)
    op.execute(
        "INSERT INTO funds_v2 "
        "SELECT id, name, fund_type, amount, cutoff_date, notes "
        "FROM funds"
    )
    op.execute("DROP TABLE funds")
    op.execute("ALTER TABLE funds_v2 RENAME TO funds")

    op.execute("DELETE FROM users WHERE username = 'admin'")
    op.drop_table("users")

    op.execute("PRAGMA foreign_keys=ON")
