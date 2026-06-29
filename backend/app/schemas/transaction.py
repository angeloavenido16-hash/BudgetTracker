"""Transaction schemas — expense/saving entries."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    fund_id: int
    category: str
    amount: float
    txn_date: str | None = None
    remarks: str | None = None


class TransactionUpdate(BaseModel):
    """Mirror of desktop update_transaction — fund_id is NOT reassignable."""
    category: str
    amount: float
    txn_date: str | None = None
    remarks: str | None = None


class Transaction(BaseModel):
    id: int
    fund_id: int
    category: str
    amount: float
    txn_date: str | None = None
    remarks: str | None = None
    created_at: datetime | None = None
    # Joined from funds.name (desktop get_transactions returns this too).
    fund_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
