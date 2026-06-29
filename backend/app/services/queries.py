"""
app/services/queries.py — async DB access helpers (user-scoped).

These are the ONLY place that touches SQLAlchemy for reads used by the
summary/report services. They return plain dict rows in exactly the shape the
DB-agnostic `summaries.compute_*` functions expect, keeping those formulas
unit-testable without a database.

All fetch functions accept a ``user_id`` to scope data to the calling user.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BpiBalance, Fund, Transaction


async def fetch_funds(session: AsyncSession, user_id: int) -> list[dict]:
    """All funds for *user* as dicts: {id, name, fund_type, amount, cutoff_date, notes}."""
    rows = (
        (await session.execute(
            select(Fund).where(Fund.user_id == user_id).order_by(Fund.id)
        ))
        .scalars()
        .all()
    )
    return [
        {
            "id": f.id,
            "name": f.name,
            "fund_type": f.fund_type,
            "amount": f.amount,
            "cutoff_date": f.cutoff_date,
            "notes": f.notes,
        }
        for f in rows
    ]


async def fetch_transactions(session: AsyncSession, user_id: int) -> list[dict]:
    """All transactions for *user* joined to their fund name.

    Shape: {id, fund_id, category, amount, txn_date, remarks, fund_name}.
    `fund_name` is needed by the report "biggest expense" insight.
    """
    stmt = (
        select(Transaction, Fund.name.label("fund_name"))
        .join(Fund, Transaction.fund_id == Fund.id)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.txn_date.asc().nulls_first(), Transaction.id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": t.id,
            "fund_id": t.fund_id,
            "category": t.category,
            "amount": t.amount,
            "txn_date": t.txn_date,
            "remarks": t.remarks,
            "fund_name": fund_name,
        }
        for t, fund_name in rows
    ]


async def fetch_latest_bpi(session: AsyncSession, user_id: int) -> float:
    """Latest bank balance for *user* (highest id wins), or 0.0 if none."""
    stmt = (
        select(BpiBalance.balance)
        .where(BpiBalance.user_id == user_id)
        .order_by(BpiBalance.id.desc())
        .limit(1)
    )
    val = (await session.execute(stmt)).scalar_one_or_none()
    return float(val) if val is not None else 0.0
