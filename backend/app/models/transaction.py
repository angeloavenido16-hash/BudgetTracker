"""Transaction model — one row per expense/saving entry."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id:        Mapped[int]   = mapped_column(primary_key=True)
    user_id:   Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=False)
    fund_id:   Mapped[int]   = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category:  Mapped[str]   = mapped_column(String, nullable=False)
    amount:    Mapped[float] = mapped_column(Float, nullable=False)
    txn_date:  Mapped[str | None] = mapped_column(String, nullable=True)
    remarks:   Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fund: Mapped["Fund"] = relationship(back_populates="transactions")
