"""
database.py  –  SQLite backend for Budget Tracker App
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "budget_tracker.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    """Create all tables if they do not exist yet."""
    with get_connection() as conn:
        cur = conn.cursor()

        # ── Expense categories (dropdown list) ──────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expense_categories (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT    NOT NULL UNIQUE
            )
        """)

        # ── Income / Fund sources ────────────────────────────────────────
        # type: 'salary' | 'bonus' | 'espp' | 'other'
        cur.execute("""
            CREATE TABLE IF NOT EXISTS funds (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL UNIQUE,
                fund_type     TEXT    NOT NULL DEFAULT 'salary',
                amount        REAL    NOT NULL DEFAULT 0,
                cutoff_date   TEXT,
                notes         TEXT
            )
        """)

        # ── Transactions (one row per expense/saving entry) ──────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_id     INTEGER NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
                category    TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                txn_date    TEXT,
                remarks     TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)

        # ── BPI bank balance snapshot ────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bpi_balance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                balance     REAL    NOT NULL,
                recorded_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)

        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Categories
# ═══════════════════════════════════════════════════════════════════════════

def get_categories():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM expense_categories ORDER BY name"
        ).fetchall()
        return [r["name"] for r in rows]


def add_category(name: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO expense_categories(name) VALUES(?)", (name,)
        )
        conn.commit()


def delete_category(name: str):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM expense_categories WHERE name=?", (name,)
        )
        conn.commit()


def seed_categories(names: list[str]):
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO expense_categories(name) VALUES(?)",
            [(n,) for n in names],
        )
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Funds (income sources)
# ═══════════════════════════════════════════════════════════════════════════

def get_funds(fund_type=None):
    with get_connection() as conn:
        if fund_type:
            rows = conn.execute(
                "SELECT * FROM funds WHERE fund_type=? ORDER BY cutoff_date DESC, name",
                (fund_type,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM funds ORDER BY cutoff_date DESC, name"
            ).fetchall()
        return [dict(r) for r in rows]


def get_fund_by_id(fund_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM funds WHERE id=?", (fund_id,)
        ).fetchone()
        return dict(row) if row else None


def add_fund(name: str, fund_type: str, amount: float,
             cutoff_date: str = None, notes: str = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO funds(name, fund_type, amount, cutoff_date, notes)
               VALUES(?,?,?,?,?)""",
            (name, fund_type, amount, cutoff_date, notes),
        )
        conn.commit()
        return cur.lastrowid


def update_fund(fund_id: int, name: str, fund_type: str, amount: float,
                cutoff_date: str = None, notes: str = None):
    with get_connection() as conn:
        conn.execute(
            """UPDATE funds SET name=?, fund_type=?, amount=?,
               cutoff_date=?, notes=? WHERE id=?""",
            (name, fund_type, amount, cutoff_date, notes, fund_id),
        )
        conn.commit()


def delete_fund(fund_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM funds WHERE id=?", (fund_id,))
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Transactions
# ═══════════════════════════════════════════════════════════════════════════

def get_transactions(fund_id: int = None):
    with get_connection() as conn:
        if fund_id:
            rows = conn.execute(
                """SELECT t.*, f.name as fund_name
                   FROM transactions t JOIN funds f ON t.fund_id=f.id
                   WHERE t.fund_id=? ORDER BY t.txn_date, t.id""",
                (fund_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT t.*, f.name as fund_name
                   FROM transactions t JOIN funds f ON t.fund_id=f.id
                   ORDER BY t.txn_date, t.id"""
            ).fetchall()
        return [dict(r) for r in rows]


def add_transaction(fund_id: int, category: str, amount: float,
                    txn_date: str = None, remarks: str = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO transactions(fund_id, category, amount, txn_date, remarks)
               VALUES(?,?,?,?,?)""",
            (fund_id, category, amount, txn_date, remarks),
        )
        conn.commit()
        return cur.lastrowid


def update_transaction(txn_id: int, category: str, amount: float,
                       txn_date: str = None, remarks: str = None):
    with get_connection() as conn:
        conn.execute(
            """UPDATE transactions SET category=?, amount=?, txn_date=?, remarks=?
               WHERE id=?""",
            (category, amount, txn_date, remarks, txn_id),
        )
        conn.commit()


def delete_transaction(txn_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
        conn.commit()


def get_fund_summary(fund_id: int) -> dict:
    """Return income, total_expenses, remaining — mirroring Excel exactly."""
    with get_connection() as conn:
        fund = conn.execute(
            "SELECT amount FROM funds WHERE id=?", (fund_id,)
        ).fetchone()
        if not fund:
            return {}
        income = fund["amount"]

        rows = conn.execute(
            "SELECT category, amount FROM transactions WHERE fund_id=?",
            (fund_id,),
        ).fetchall()

        total_expenses = sum(r["amount"] for r in rows)
        savings    = sum(r["amount"] for r in rows
                         if r["category"].lower() == "savings"
                         and r["amount"] > 0)
        carry_over = sum(r["amount"] for r in rows
                         if r["category"].lower() in ("carry over", "carry_over")
                         and r["amount"] > 0)
        house      = sum(r["amount"] for r in rows
                         if r["category"].lower() == "house")

        return {
            "income":        income,
            "expenses":      round(total_expenses, 2),
            "savings":       round(savings, 2),
            "house":         round(house, 2),
            "carry_over":    round(carry_over, 2),
            "remaining":     round(income - total_expenses, 2),
        }


def get_all_fund_summaries() -> dict[int, dict]:
    """Bulk version of get_fund_summary — fetches ALL funds in 2 queries.

    Returns a dict keyed by fund_id.  Replaces the N+1 loop in FundsView.refresh().
    """
    with get_connection() as conn:
        funds = conn.execute("SELECT id, amount FROM funds").fetchall()

        # All transactions in one shot
        txn_rows = conn.execute(
            "SELECT fund_id, category, amount FROM transactions"
        ).fetchall()

    # Group transactions by fund_id in Python
    from collections import defaultdict
    by_fund: dict[int, list] = defaultdict(list)
    for r in txn_rows:
        by_fund[r["fund_id"]].append(r)

    result = {}
    for f in funds:
        fid    = f["id"]
        income = f["amount"]
        rows   = by_fund[fid]

        total_expenses = sum(r["amount"] for r in rows)
        savings    = sum(r["amount"] for r in rows
                         if r["category"].lower() == "savings"
                         and r["amount"] > 0)
        carry_over = sum(r["amount"] for r in rows
                         if r["category"].lower() in ("carry over", "carry_over")
                         and r["amount"] > 0)
        house      = sum(r["amount"] for r in rows
                         if r["category"].lower() == "house")

        result[fid] = {
            "income":        income,
            "expenses":      round(total_expenses, 2),
            "savings":       round(savings, 2),
            "house":         round(house, 2),
            "carry_over":    round(carry_over, 2),
            "remaining":     round(income - total_expenses, 2),
        }
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Dashboard aggregates
# ═══════════════════════════════════════════════════════════════════════════

def get_dashboard_totals():
    with get_connection() as conn:
        # ── Total Income ─────────────────────────────────────────────────
        # Sum of Amount column for non-"other" funds only
        total_income = conn.execute(
            """SELECT COALESCE(SUM(amount),0) FROM funds
               WHERE fund_type != 'other'"""
        ).fetchone()[0]

        # ── Total Expenses ────────────────────────────────────────────────
        # Sum of Expenses column (raw SUM of all txn amounts) for non-"other" funds
        total_expenses = conn.execute(
            """SELECT COALESCE(SUM(t.amount),0)
               FROM transactions t
               JOIN funds f ON t.fund_id = f.id
               WHERE f.fund_type != 'other'"""
        ).fetchone()[0]

        # ── Total Savings ─────────────────────────────────────────────────
        # Sum of Remaining column for "other" funds only
        # = SUM(other funds.amount) - SUM(their transactions)
        other_income = conn.execute(
            """SELECT COALESCE(SUM(amount),0) FROM funds
               WHERE fund_type = 'other'"""
        ).fetchone()[0]
        other_txn = conn.execute(
            """SELECT COALESCE(SUM(t.amount),0)
               FROM transactions t
               JOIN funds f ON t.fund_id = f.id
               WHERE f.fund_type = 'other'"""
        ).fetchone()[0]
        total_savings = other_income - other_txn

        # ── Net Remaining ─────────────────────────────────────────────────
        # Sum of remaining across ALL funds: SUM(funds.amount) - SUM(all txn amounts)
        all_income = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM funds"
        ).fetchone()[0]
        net_txn_flow = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions"
        ).fetchone()[0]
        net_remaining = all_income - net_txn_flow

        # ── Non-other Remaining ───────────────────────────────────────────
        # Sum of Remaining column for non-"other" funds only
        # = SUM(fund.amount) - SUM(txn.amount) for those funds
        non_other_income = total_income   # already computed above
        non_other_txn = conn.execute(
            """SELECT COALESCE(SUM(t.amount),0)
               FROM transactions t
               JOIN funds f ON t.fund_id = f.id
               WHERE f.fund_type != 'other'"""
        ).fetchone()[0]
        non_other_remaining = non_other_income - non_other_txn

        fund_count = conn.execute(
            "SELECT COUNT(*) FROM funds"
        ).fetchone()[0]

        return {
            "total_income":        total_income,
            "total_expenses":      total_expenses,
            "total_savings":       total_savings,
            "net_remaining":       net_remaining,
            "non_other_remaining": non_other_remaining,
            "fund_count":          fund_count,
        }


def get_expense_by_category(fund_id=None):
    """Return list of (category, total) sorted descending."""
    with get_connection() as conn:
        if fund_id:
            rows = conn.execute(
                """SELECT category, SUM(amount) as total
                   FROM transactions
                   WHERE fund_id=? AND amount>0
                   GROUP BY category ORDER BY total DESC""",
                (fund_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT category, SUM(amount) as total
                   FROM transactions
                   WHERE amount>0
                   GROUP BY category ORDER BY total DESC"""
            ).fetchall()
        return [(r["category"], r["total"]) for r in rows]


def get_spending_over_time():
    """Monthly totals across all transactions."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT SUBSTR(txn_date,1,7) as month,
                      SUM(CASE WHEN amount>0 THEN amount ELSE 0 END) as total
               FROM transactions
               WHERE txn_date IS NOT NULL
               GROUP BY month ORDER BY month"""
        ).fetchall()
        return [(r["month"], r["total"]) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
# BPI Balance
# ═══════════════════════════════════════════════════════════════════════════

def update_bpi_balance(balance: float):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO bpi_balance(balance) VALUES(?)", (balance,)
        )
        conn.commit()


def get_latest_bpi_balance():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT balance FROM bpi_balance ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["balance"] if row else 0.0
