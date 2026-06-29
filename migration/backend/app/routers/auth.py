"""Auth router — POST /auth/login → JWT."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import LoginRequest, Token
from app.security import create_access_token, verify_credentials

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest) -> Token:
    """Validate the single-user credentials and return a bearer token."""
    if not verify_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return Token(access_token=create_access_token(body.username))
