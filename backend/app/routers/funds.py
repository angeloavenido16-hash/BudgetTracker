"""Funds router — CRUD + per-fund summaries (user-scoped).

Mirrors desktop database.get_funds / get_fund_by_id / add_fund / update_fund /
delete_fund / get_fund_summary / get_all_fund_summaries.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Fund as FundModel
from app.schemas import Fund, FundCreate, FundSummary, FundUpdate
from app.security import get_current_user
from app.services import queries, summaries

router = APIRouter(prefix="/funds", tags=["funds"])


async def _get_or_404(
    session: AsyncSession, fund_id: int, user_id: int
) -> FundModel:
    fund = await session.scalar(
        select(FundModel).where(
            FundModel.id == fund_id, FundModel.user_id == user_id
        )
    )
    if fund is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fund not found")
    return fund


@router.get("", response_model=list[Fund])
async def list_funds(
    user_id: int = Depends(get_current_user),
    fund_type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(FundModel)
        .where(FundModel.user_id == user_id)
        .order_by(
            FundModel.cutoff_date.desc().nulls_last(), FundModel.name
        )
    )
    if fund_type:
        stmt = stmt.where(FundModel.fund_type == fund_type)
    return (await session.execute(stmt)).scalars().all()


@router.get("/summaries", response_model=dict[int, FundSummary])
async def fund_summaries(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    funds = await queries.fetch_funds(session, user_id)
    txns = await queries.fetch_transactions(session, user_id)
    return summaries.compute_all_fund_summaries(funds, txns)


@router.get("/{fund_id}", response_model=Fund)
async def get_fund(
    fund_id: int,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _get_or_404(session, fund_id, user_id)


@router.get("/{fund_id}/summary", response_model=FundSummary)
async def fund_summary(
    fund_id: int,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    fund = await _get_or_404(session, fund_id, user_id)
    txns = await queries.fetch_transactions(session, user_id)
    own = [t for t in txns if t["fund_id"] == fund_id]
    return summaries.compute_fund_summary(fund.amount, own)


@router.post("", response_model=Fund, status_code=status.HTTP_201_CREATED)
async def create_fund(
    body: FundCreate,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    fund = FundModel(**body.model_dump(), user_id=user_id)
    session.add(fund)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Fund name already exists")
    await session.refresh(fund)
    return fund


@router.put("/{fund_id}", response_model=Fund)
async def update_fund(
    fund_id: int,
    body: FundUpdate,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    fund = await _get_or_404(session, fund_id, user_id)
    for key, value in body.model_dump().items():
        setattr(fund, key, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Fund name already exists")
    await session.refresh(fund)
    return fund


@router.delete("/{fund_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fund(
    fund_id: int,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    fund = await _get_or_404(session, fund_id, user_id)
    await session.delete(fund)
    await session.commit()
