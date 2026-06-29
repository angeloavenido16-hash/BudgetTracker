"""ExpenseCategory model — per-user dropdown list of categories."""
from __future__ import annotations
from sqlalchemy import Boolean, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id:        Mapped[int] = mapped_column(primary_key=True)
    user_id:   Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name:      Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_expense_categories_user_id_name"),
    )
