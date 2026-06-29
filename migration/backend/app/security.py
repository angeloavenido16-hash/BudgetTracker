"""
app/security.py — JWT auth for the single-user app.

The app has exactly one user (APP_USERNAME / APP_PASSWORD from settings). On
login we verify the credentials and mint a JWT; every protected route depends on
`get_current_user`, which validates the bearer token.

Password hashing uses the `bcrypt` library directly (not passlib) — the app
only ever hashes/verifies one password, and passlib 1.7.x is incompatible with
modern bcrypt 4.1+, so the thin direct call is both simpler and more robust.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings

# Token endpoint the OpenAPI "Authorize" button posts to.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def _to_bytes(password: str) -> bytes:
    """bcrypt only considers the first 72 bytes — truncate to stay in spec."""
    return password.encode("utf-8")[:72]


# Hash the configured password once at import (cheap, single user).
_PASSWORD_HASH = bcrypt.hashpw(_to_bytes(settings.APP_PASSWORD), bcrypt.gensalt())


def verify_credentials(username: str, password: str) -> bool:
    """True if the supplied credentials match the configured single user."""
    if username != settings.APP_USERNAME:
        return False
    return bcrypt.checkpw(_to_bytes(password), _PASSWORD_HASH)


def create_access_token(subject: str) -> str:
    """Mint a signed JWT whose `sub` is the username."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """FastAPI dependency — decode + validate the bearer token, return username."""
    creds_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise creds_error
    except JWTError:
        raise creds_error
    return username
