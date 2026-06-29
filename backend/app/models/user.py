"""User model — multi-user accounts."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id:            Mapped[int] = mapped_column(primary_key=True)
    username:      Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_admin:      Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active:     Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at:    Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
