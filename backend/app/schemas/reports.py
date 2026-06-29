"""Reports schemas — statistical aggregates (Overview / Category / Flows).

The tuple fields (busiest_month, top_category, most_frequent, …) serialize to
JSON arrays, matching the frontend's MonthPoint / CategoryPoint `[string, number]`
types in api/types.ts.
"""
from __future__ import annotations

from pydantic import BaseModel


class BiggestExpense(BaseModel):
    amount: float
    category: str
    txn_date: str | None = None
    fund_name: str | None = None


class ReportOverview(BaseModel):
    total_spent: float
    txn_count: int
    avg_txn: float
    savings: float
    avg_monthly: float
    active_months: int
    biggest: BiggestExpense | None = None
    busiest_month: tuple[str, float] | None = None
    quietest_month: tuple[str, float] | None = None
    mom_change: float | None = None
    latest_month: tuple[str, float] | None = None
    top_category: tuple[str, float] | None = None
    top_category_share: float
    # (category, count) — count is an int.
    most_frequent: tuple[str, int] | None = None


class CategoryStat(BaseModel):
    category: str
    total: float
    count: int
    avg: float
    max: float
    share: float


class FundFlow(BaseModel):
    id: int
    name: str
    out_flow: float
    in_flow: float
    net: float
    count: int
