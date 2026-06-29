"""Dashboard schemas — headline totals + chart points."""
from __future__ import annotations

from pydantic import BaseModel


class DashboardTotals(BaseModel):
    total_income: float
    total_expenses: float
    total_savings: float
    net_remaining: float
    non_other_remaining: float
    # bpi_balance − non_other_remaining (red in the UI when positive).
    missing_expenses: float
    bpi_balance: float
    fund_count: int


class MonthTotal(BaseModel):
    """A point in the 'spending over time' line chart."""
    month: str  # "YYYY-MM"
    total: float


class CategoryTotal(BaseModel):
    """A slice in the 'expense by category' pie chart."""
    category: str
    total: float
