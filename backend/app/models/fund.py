"""Fund model — income sources (salary / bonus / espp / other)."""
from __future__ import annotations
from sqlalchemy import String, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Fund(Base):
    __tablename__ = "funds"

    id:          Mapped[int]   = mapped_column(primary_key=True)
    user_id:     Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=False)
    name:        Mapped[str]   = mapped_column(String, nullable=False)
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

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_funds_user_id_name"),
    )
