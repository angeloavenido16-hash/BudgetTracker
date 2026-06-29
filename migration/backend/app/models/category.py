"""ExpenseCategory model — dropdown list of categories."""
from __future__ import annotations
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id:   Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
