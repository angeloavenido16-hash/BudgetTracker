"""Dashboard router — headline totals + chart data + year list (user-scoped).

Mirrors desktop database.get_dashboard_totals / get_spending_over_time /
get_expense_by_category / get_transaction_years.  The math lives in
services.summaries (parity-locked); this layer only fetches rows + shapes output.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import CategoryTotal, DashboardTotals, MonthTotal
from app.security import get_current_user
from app.services import queries, summaries

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/totals", response_model=DashboardTotals)
async def dashboard_totals(
    user_id: int = Depends(get_current_user),
    year: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    funds = await queries.fetch_funds(session, user_id)
    txns = await queries.fetch_transactions(session, user_id)
    bpi = await queries.fetch_latest_bpi(session, user_id)
    return summaries.compute_dashboard_totals(funds, txns, bpi, year)


@router.get("/spending-over-time", response_model=list[MonthTotal])
async def spending_over_time(
    user_id: int = Depends(get_current_user),
    year: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    txns = await queries.fetch_transactions(session, user_id)
    points = summaries.compute_spending_over_time(txns, year)
    return [{"month": m, "total": v} for m, v in points]


@router.get("/expense-by-category", response_model=list[CategoryTotal])
async def expense_by_category(
    user_id: int = Depends(get_current_user),
    fund_id: int | None = None,
    year: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    txns = await queries.fetch_transactions(session, user_id)
    rows = summaries.compute_expense_by_category(txns, fund_id, year)
    return [{"category": c, "total": v} for c, v in rows]


@router.get("/years", response_model=list[str])
async def transaction_years(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    txns = await queries.fetch_transactions(session, user_id)
    return summaries.compute_transaction_years(txns)


@router.get("/category-over-time", response_model=list[MonthTotal])
async def category_over_time(
    user_id: int = Depends(get_current_user),
    category: str = "",
    year: str | None = None,
    sign: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    txns = await queries.fetch_transactions(session, user_id)
    points = summaries.compute_category_over_time(txns, category, year, sign)
    return [{"month": m, "total": v} for m, v in points]
