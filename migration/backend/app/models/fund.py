"""Fund model — income sources (salary / bonus / espp / other)."""
from __future__ import annotations
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Fund(Base):
    __tablename__ = "funds"

    id:          Mapped[int]   = mapped_column(primary_key=True)
    name:        Mapped[str]   = mapped_column(String, unique=True, nullable=False)
    # server_default (not just Python default) mirrors the desktop SQLite schema
    # (DEFAULT 'salary' / DEFAULT 0) so Alembic --autogenerate stays churn-free.
    fund_type:   Mapped[str]   = mapped_column(
        String, nullable=False, default="salary", server_default="salary"
    )
    amount:      Mapped[float] = mapped_column(
        Float, nullable=False, default=0, server_default="0"
    )
    cutoff_date: Mapped[str | None] = mapped_column(String, nullable=True)
    notes:       Mapped[str | None] = mapped_column(Text, nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )
