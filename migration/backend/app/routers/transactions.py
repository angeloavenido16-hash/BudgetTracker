"""Transactions router — CRUD.

Mirrors desktop database.get_transactions / add_transaction /
update_transaction / delete_transaction.  List responses include the joined
`fund_name` (like the desktop SELECT t.*, f.name).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Fund as FundModel
from app.models import Transaction as TxnModel
from app.schemas import Transaction, TransactionCreate, TransactionUpdate
from app.security import get_current_user

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Depends(get_current_user)],
)


async def _serialize(session: AsyncSession, txn: TxnModel) -> dict:
    """Attach fund_name so the response matches the list shape."""
    fund_name = await session.scalar(
        select(FundModel.name).where(FundModel.id == txn.fund_id)
    )
    return {
        "id": txn.id,
        "fund_id": txn.fund_id,
        "category": txn.category,
        "amount": txn.amount,
        "txn_date": txn.txn_date,
        "remarks": txn.remarks,
        "created_at": txn.created_at,
        "fund_name": fund_name,
    }


@router.get("", response_model=list[Transaction])
async def list_transactions(
    fund_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(TxnModel, FundModel.name.label("fund_name"))
        .join(FundModel, TxnModel.fund_id == FundModel.id)
        # SQLite orders NULL txn_date FIRST in ascending; Postgres orders them
        # LAST by default. Force NULLS FIRST so the web list matches the desktop
        # app exactly (≈80 undated rows would otherwise jump to the bottom).
        .order_by(TxnModel.txn_date.asc().nulls_first(), TxnModel.id)
    )
    if fund_id:
        stmt = stmt.where(TxnModel.fund_id == fund_id)
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": t.id,
            "fund_id": t.fund_id,
            "category": t.category,
            "amount": t.amount,
            "txn_date": t.txn_date,
            "remarks": t.remarks,
            "created_at": t.created_at,
            "fund_name": fund_name,
        }
        for t, fund_name in rows
    ]


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate, session: AsyncSession = Depends(get_session)
):
    # Validate the parent fund exists (FK would error, but 404 is clearer).
    if await session.get(FundModel, body.fund_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fund not found")
    txn = TxnModel(**body.model_dump())
    session.add(txn)
    await session.commit()
    await session.refresh(txn)
    return await _serialize(session, txn)


@router.put("/{txn_id}", response_model=Transaction)
async def update_transaction(
    txn_id: int,
    body: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
):
    txn = await session.get(TxnModel, txn_id)
    if txn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    for key, value in body.model_dump().items():
        setattr(txn, key, value)
    await session.commit()
    await session.refresh(txn)
    return await _serialize(session, txn)


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    txn_id: int, session: AsyncSession = Depends(get_session)
):
    txn = await session.get(TxnModel, txn_id)
    if txn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    await session.delete(txn)
    await session.commit()
