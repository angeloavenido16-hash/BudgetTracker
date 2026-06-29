"""
app/security.py — JWT auth via the users table.

On login we verify credentials against the `users` table and mint a JWT whose
`sub` claim is the user_id. Every protected route depends on `get_current_user`,
which decodes the token, looks up the user, and returns the user_id.

Password hashing uses bcrypt directly (not passlib).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def _to_bytes(password: str) -> bytes:
    """bcrypt only considers the first 72 bytes — truncate to stay in spec."""
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    """Hash a password with bcrypt, return the hash as a string."""
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """True if the password matches the stored hash."""
    return bcrypt.checkpw(_to_bytes(password), password_hash.encode("utf-8"))


async def verify_credentials(
    username: str, password: str, session: AsyncSession
) -> int | None:
    """Verify credentials against the users table. Returns user_id or None."""
    user = await session.scalar(
        select(User).where(User.username == username)
    )
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user.id


def create_access_token(subject: str, extra: dict | None = None) -> str:
    """Mint a signed JWT whose `sub` is the user_id.

    Any keys in *extra* are also included in the JWT payload (e.g. is_admin).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> int:
    """Decode the bearer token, look up user, check active, return user_id."""
    creds_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise creds_error
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        raise creds_error

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise creds_error
    return user_id


async def get_admin_user(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user),
) -> User:
    """Require the authenticated user to be an admin. Returns User model."""
    user = await session.get(User, user_id)
    if user is None or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
