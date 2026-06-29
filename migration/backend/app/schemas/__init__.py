"""Pydantic schemas — request/response models for the API.

Re-exported here so routers can do `from app.schemas import Fund, ...`.
Shapes mirror docs/API_CONTRACT.md and the frontend's api/types.ts.
"""
from app.schemas.auth import LoginRequest, Token
from app.schemas.fund import Fund, FundCreate, FundUpdate, FundSummary, FundType
from app.schemas.transaction import (
    Transaction, TransactionCreate, TransactionUpdate,
)
from app.schemas.category import CategoryCreate
from app.schemas.bpi import BpiBalance, BpiUpdate
from app.schemas.dashboard import DashboardTotals, MonthTotal, CategoryTotal
from app.schemas.reports import (
    BiggestExpense, ReportOverview, CategoryStat, FundFlow,
)

__all__ = [
    "LoginRequest", "Token",
    "Fund", "FundCreate", "FundUpdate", "FundSummary", "FundType",
    "Transaction", "TransactionCreate", "TransactionUpdate",
    "CategoryCreate",
    "BpiBalance", "BpiUpdate",
    "DashboardTotals", "MonthTotal", "CategoryTotal",
    "BiggestExpense", "ReportOverview", "CategoryStat", "FundFlow",
]
