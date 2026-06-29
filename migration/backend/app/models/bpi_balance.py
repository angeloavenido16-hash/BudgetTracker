"""BpiBalance model — bank balance snapshots (latest row wins)."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BpiBalance(Base):
    __tablename__ = "bpi_balance"

    id:      Mapped[int]   = mapped_column(primary_key=True)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
