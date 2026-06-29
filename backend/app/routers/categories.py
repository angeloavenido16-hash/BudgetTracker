"""Categories router — list / add / archive / restore expense categories (user-scoped).

Mirrors desktop database.get_categories / add_category (INSERT OR IGNORE) /
delete_category (by name). DELETE now soft-deletes (archive).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ExpenseCategory
from app.schemas import CategoryCreate
from app.security import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
async def list_categories(
    user_id: int = Depends(get_current_user),
    all: bool = Query(False, description="Include archived"),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(ExpenseCategory).where(
        ExpenseCategory.user_id == user_id
    ).order_by(ExpenseCategory.name)
    if not all:
        stmt = stmt.where(ExpenseCategory.is_active == True)
    result = (await session.execute(stmt)).scalars().all()
    if not all:
        return [r.name for r in result]
    return [{"name": r.name, "is_active": r.is_active} for r in result]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_category(
    body: CategoryCreate,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Idempotent add — reactivates if previously archived."""
    existing = await session.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.name == body.name,
            ExpenseCategory.user_id == user_id,
        )
    )
    if existing is None:
        session.add(ExpenseCategory(name=body.name, user_id=user_id))
    elif not existing.is_active:
        existing.is_active = True
    await session.commit()
    return {"name": body.name}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_category(
    name: str,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Soft-delete (archive) — hides from dropdowns but preserves data."""
    obj = await session.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.name == name,
            ExpenseCategory.user_id == user_id,
        )
    )
    if obj is not None:
        obj.is_active = False
        await session.commit()


@router.patch("/{name}/restore", status_code=status.HTTP_200_OK)
async def restore_category(
    name: str,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Restore an archived category back to active."""
    obj = await session.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.name == name,
            ExpenseCategory.user_id == user_id,
        )
    )
    if obj is not None:
        obj.is_active = True
        await session.commit()
    return {"name": name}
