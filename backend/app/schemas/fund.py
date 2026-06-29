"""Fund schemas — income sources + per-fund summary."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

# Allowed fund types (mirrors the desktop app + frontend FundType union).
FundType = Literal["salary", "bonus", "espp", "other"]


class FundBase(BaseModel):
    name: str
    # Strict on input so typos are rejected; the response model (Fund) is lenient.
    fund_type: FundType = "salary"
    amount: float = 0.0
    cutoff_date: str | None = None
    notes: str | None = None


class FundCreate(FundBase):
    pass


class FundUpdate(FundBase):
    pass


class Fund(BaseModel):
    """Response shape — lenient fund_type so unexpected legacy values never 500."""
    id: int
    name: str
    fund_type: str
    amount: float
    cutoff_date: str | None = None
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FundSummary(BaseModel):
    income: float
    expenses: float
    savings: float
    house: float
    carry_over: float
    remaining: float
