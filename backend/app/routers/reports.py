"""Reports router — statistical aggregates (Overview / Category / Flows), user-scoped.

Mirrors desktop database.get_report_overview / get_category_statistics /
get_fund_flows.  All three accept the shared Year / Month / Fund filters;
fund-flows ignores fund_id (it IS the per-fund view).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import CategoryStat, FundFlow, ReportOverview
from app.security import get_current_user
from app.services import queries, summaries

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/overview", response_model=ReportOverview)
async def report_overview(
    user_id: int = Depends(get_current_user),
    year: str | None = None,
    month: str | None = None,
    fund_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    txns = await queries.fetch_transactions(session, user_id)
    return summaries.compute_report_overview(txns, year, fund_id, month)


@router.get("/category-stats", response_model=list[CategoryStat])
async def category_stats(
    user_id: int = Depends(get_current_user),
    year: str | None = None,
    month: str | None = None,
    fund_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    txns = await queries.fetch_transactions(session, user_id)
    return summaries.compute_category_statistics(txns, year, fund_id, month)


@router.get("/fund-flows", response_model=list[FundFlow])
async def fund_flows(
    user_id: int = Depends(get_current_user),
    year: str | None = None,
    month: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    funds = await queries.fetch_funds(session, user_id)
    txns = await queries.fetch_transactions(session, user_id)
    return summaries.compute_fund_flows(funds, txns, year, month)
