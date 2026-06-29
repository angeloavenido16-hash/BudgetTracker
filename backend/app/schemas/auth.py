"""Auth schemas — login + registration."""
from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime | None = None


class UserAdminResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool
    created_at: datetime | None = None


class PasswordResetRequest(BaseModel):
    password: str
