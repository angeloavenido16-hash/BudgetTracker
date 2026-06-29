"""Temp: re-verify ported formulas vs live desktop database.py after bug fixes."""
import sys
sys.path.insert(0, "migration/backend")
sys.stdout.reconfigure(encoding="utf-8")

import database as db
from app.services import summaries as S

funds = db.get_funds()
txns_all = db.get_transactions()

mism = 0
def chk(name, a, b, tol=0.01):
    global mism
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if abs((a or 0) - (b or 0)) > tol:
            mism += 1; print(f"  MISMATCH {name}: desktop={a} ported={b}")
    elif a != b:
        mism += 1; print(f"  MISMATCH {name}: desktop={a} ported={b}")

# Report overview — including most_frequent and top_category (tuple compare)
ro_desk = db.get_report_overview()
ro_port = S.compute_report_overview(
    [{"fund_id": t["fund_id"], "fund_name": t["fund_name"], "category": t["category"],
      "amount": t["amount"], "txn_date": t["txn_date"]} for t in txns_all])
for k in ("total_spent", "txn_count", "avg_txn", "savings", "avg_monthly",
          "active_months", "top_category_share"):
    chk("overview." + k, ro_desk[k] or 0, ro_port[k] or 0)
chk("overview.most_frequent", tuple(ro_desk["most_frequent"]) if ro_desk["most_frequent"] else None,
    tuple(ro_port["most_frequent"]) if ro_port["most_frequent"] else None)
chk("overview.top_category", tuple(ro_desk["top_category"]) if ro_desk["top_category"] else None,
    tuple(ro_port["top_category"]) if ro_port["top_category"] else None)
chk("overview.busiest_month", tuple(ro_desk["busiest_month"]) if ro_desk["busiest_month"] else None,
    tuple(ro_port["busiest_month"]) if ro_port["busiest_month"] else None)

# Per-year spot checks too
for yr in db.get_transaction_years():
    d = db.get_report_overview(year=yr)
    p = S.compute_report_overview(
        [{"fund_id": t["fund_id"], "fund_name": t["fund_name"], "category": t["category"],
          "amount": t["amount"], "txn_date": t["txn_date"]} for t in txns_all], year=yr)
    chk(f"overview[{yr}].total_spent", d["total_spent"], p["total_spent"])
    chk(f"overview[{yr}].most_frequent",
        tuple(d["most_frequent"]) if d["most_frequent"] else None,
        tuple(p["most_frequent"]) if p["most_frequent"] else None)

print()
print("REAL-DATA PARITY (overview):", "ALL MATCH" if mism == 0 else f"{mism} MISMATCHES")
