"""BPI balance router — GET latest / PUT new snapshot.

Mirrors desktop database.get_latest_bpi_balance / update_bpi_balance.
A PUT inserts a NEW snapshot row (history is preserved; latest id wins).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import BpiBalance as BpiModel
from app.schemas import BpiBalance, BpiUpdate
from app.security import get_current_user

router = APIRouter(
    prefix="/bpi-balance",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=BpiBalance)
async def get_bpi_balance(session: AsyncSession = Depends(get_session)):
    row = await session.scalar(
        select(BpiModel).order_by(BpiModel.id.desc()).limit(1)
    )
    if row is None:
        return BpiBalance(balance=0.0, recorded_at=None)
    return row


@router.put("", response_model=BpiBalance)
async def set_bpi_balance(
    body: BpiUpdate, session: AsyncSession = Depends(get_session)
):
    snapshot = BpiModel(balance=body.balance)
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot
