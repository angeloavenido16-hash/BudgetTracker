import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("migration/backend").resolve()))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "x")
os.environ.setdefault("APP_USERNAME", "a")
os.environ.setdefault("APP_PASSWORD", "b")

from app.schemas import DashboardTotals, FundSummary, ReportOverview  # noqa: E402
from app.services import summaries  # noqa: E402

issues = []
funds = [
    {"id": 1, "fund_type": "salary", "amount": 100, "name": "S"},
    {"id": 2, "fund_type": "other", "amount": 50, "name": "O"},
]
txns = [{"fund_id": 1, "amount": 20, "category": "x", "txn_date": "2025-01-01"}]

d = summaries.compute_dashboard_totals(funds, txns, bpi_balance=70)
try:
    DashboardTotals(**d)
except Exception as ex:  # noqa: BLE001
    issues.append(f"DashboardTotals: {ex}")

o = summaries.compute_report_overview(txns, None, None, None)
try:
    ov = ReportOverview(**o)
    if ov.most_frequent is not None:
        a, b = ov.most_frequent
        if not (isinstance(a, str) and isinstance(b, int)):
            issues.append(f"most_frequent types: {ov.most_frequent!r}")
except Exception as ex:  # noqa: BLE001
    issues.append(f"ReportOverview: {ex}")

fs = summaries.compute_fund_summary(100, txns)
try:
    FundSummary(**fs)
except Exception as ex:  # noqa: BLE001
    issues.append(f"FundSummary: {ex}")

if issues:
    print("ISSUES:")
    for i in issues:
        print("  -", i)
    sys.exit(1)
print("SERVICE-SCHEMA CONTRACT: ALL OK")
print("dashboard keys:", ", ".join(sorted(d)))
