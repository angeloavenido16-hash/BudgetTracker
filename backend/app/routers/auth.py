"""Auth router — login, registration, user management (admin-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import BpiBalance, ExpenseCategory, Fund, Transaction, User
from app.schemas import LoginRequest, PasswordResetRequest, RegisterRequest, Token
from app.schemas.auth import MeResponse, UserAdminResponse
from app.security import (
    create_access_token,
    get_admin_user,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Default categories seeded for every new user.
DEFAULT_CATEGORIES = ["budget", "savings", "electric bill", "water bill"]


@router.post("/login", response_model=Token)
async def login(
    body: LoginRequest, session: AsyncSession = Depends(get_session)
) -> Token:
    """Validate credentials against the users table and return a bearer token."""
    user = await session.scalar(
        select(User).where(User.username == body.username)
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
        )
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return Token(
        access_token=create_access_token(
            str(user.id), extra={"is_admin": user.is_admin}
        )
    )


@router.get("/me", response_model=MeResponse)
async def me(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    """Return the current user's profile."""
    user = await session.get(User, user_id)
    return MeResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
):
    """Admin-only: create a new user with default categories."""
    existing = await session.scalar(
        select(User).where(User.username == body.username)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.flush()

    for cat_name in DEFAULT_CATEGORIES:
        session.add(
            ExpenseCategory(
                name=cat_name, user_id=user.id, is_active=True
            )
        )

    await session.commit()
    return {"username": body.username}


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
):
    """Admin-only: list all user accounts."""
    users = (
        (await session.execute(select(User).order_by(User.created_at)))
        .scalars()
        .all()
    )
    return [
        UserAdminResponse(
            id=u.id,
            username=u.username,
            is_admin=u.is_admin,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.delete("/users/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    target_id: int,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(get_admin_user),
):
    """Admin-only: permanently delete a user and all their data."""
    if target_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete yourself")
    user = await session.get(User, target_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Cascade-delete user's data — order matters for FK constraints
    fund_ids = (
        (await session.execute(
            select(Fund.id).where(Fund.user_id == target_id)
        ))
        .scalars()
        .all()
    )
    if fund_ids:
        await session.execute(
            Transaction.__table__.delete().where(
                Transaction.fund_id.in_(fund_ids)
            )
        )
        await session.execute(
            Transaction.__table__.delete().where(
                Transaction.user_id == target_id
            )
        )
        await session.execute(
            Fund.__table__.delete().where(Fund.user_id == target_id)
        )
    else:
        await session.execute(
            Transaction.__table__.delete().where(
                Transaction.user_id == target_id
            )
        )

    await session.execute(
        ExpenseCategory.__table__.delete().where(
            ExpenseCategory.user_id == target_id
        )
    )
    await session.execute(
        BpiBalance.__table__.delete().where(
            BpiBalance.user_id == target_id
        )
    )
    await session.delete(user)
    await session.commit()


@router.patch("/users/{target_id}/deactivate", response_model=UserAdminResponse)
async def deactivate_user(
    target_id: int,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(get_admin_user),
):
    """Admin-only: deactivate a user (prevents login, preserves data)."""
    if target_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot deactivate yourself")
    user = await session.get(User, target_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = False
    await session.commit()
    return UserAdminResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.patch("/users/{target_id}/activate", response_model=UserAdminResponse)
async def activate_user(
    target_id: int,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(get_admin_user),
):
    """Admin-only: reactivate a deactivated user."""
    user = await session.get(User, target_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = True
    await session.commit()
    return UserAdminResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.patch("/users/{target_id}/password", status_code=status.HTTP_200_OK)
async def reset_password(
    target_id: int,
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
):
    """Admin-only: reset a user's password."""
    user = await session.get(User, target_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.password_hash = hash_password(body.password)
    await session.commit()
    return {"username": user.username}
