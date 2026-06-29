"""Categories router — list / add / delete expense categories.

Mirrors desktop database.get_categories / add_category (INSERT OR IGNORE) /
delete_category (by name).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ExpenseCategory
from app.schemas import CategoryCreate
from app.security import get_current_user

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[str])
async def list_categories(session: AsyncSession = Depends(get_session)):
    stmt = select(ExpenseCategory.name).order_by(ExpenseCategory.name)
    return list((await session.execute(stmt)).scalars().all())


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_category(
    body: CategoryCreate, session: AsyncSession = Depends(get_session)
):
    """Idempotent add — silently ignores duplicates (like INSERT OR IGNORE)."""
    exists = await session.scalar(
        select(ExpenseCategory).where(ExpenseCategory.name == body.name)
    )
    if exists is None:
        session.add(ExpenseCategory(name=body.name))
        await session.commit()
    return {"name": body.name}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(name: str, session: AsyncSession = Depends(get_session)):
    obj = await session.scalar(
        select(ExpenseCategory).where(ExpenseCategory.name == name)
    )
    if obj is not None:
        await session.delete(obj)
        await session.commit()
