"""Temp: cross-check ported migration formulas vs live desktop database.py on real data."""
import sys
sys.path.insert(0, "migration/backend")
sys.stdout.reconfigure(encoding="utf-8")

import database as db
from app.services import summaries as S

funds = db.get_funds()
txns_all = db.get_transactions()
bpi = db.get_latest_bpi_balance()

mism = 0
def chk(name, a, b, tol=0.01):
    global mism
    if abs((a or 0) - (b or 0)) > tol:
        mism += 1
        print(f"  MISMATCH {name}: desktop={a} ported={b}")

# 1) Dashboard totals
d_desk = db.get_dashboard_totals()
d_port = S.compute_dashboard_totals(
    [{"id": f["id"], "fund_type": f["fund_type"], "amount": f["amount"]} for f in funds],
    [{"fund_id": t["fund_id"], "amount": t["amount"]} for t in txns_all], bpi)
for k in ("total_income", "total_expenses", "total_savings", "net_remaining", "non_other_remaining"):
    chk("dash." + k, d_desk[k], d_port[k])

# 2) Spending over time
sot_desk = db.get_spending_over_time()
sot_port = S.compute_spending_over_time([{"txn_date": t["txn_date"], "amount": t["amount"]} for t in txns_all])
chk("spending_months_count", len(sot_desk), len(sot_port))
for (m1, v1), (m2, v2) in zip(sot_desk, sot_port):
    chk(f"spending[{m1}]", v1, v2)

# 3) Expense by category
ebc_desk = dict(db.get_expense_by_category())
ebc_port = dict(S.compute_expense_by_category(
    [{"category": t["category"], "amount": t["amount"], "fund_id": t["fund_id"], "txn_date": t["txn_date"]} for t in txns_all]))
chk("ebc_count", len(ebc_desk), len(ebc_port))
for c, v in ebc_desk.items():
    chk(f"ebc[{c}]", v, ebc_port.get(c, -1))

# 4) Years
chk("years", len(db.get_transaction_years()),
    len(S.compute_transaction_years([{"txn_date": t["txn_date"]} for t in txns_all])))

# 5) Report overview
ro_desk = db.get_report_overview()
ro_port = S.compute_report_overview(
    [{"fund_id": t["fund_id"], "fund_name": t["fund_name"], "category": t["category"],
      "amount": t["amount"], "txn_date": t["txn_date"]} for t in txns_all])
for k in ("total_spent", "txn_count", "avg_txn", "savings", "avg_monthly", "active_months", "top_category_share"):
    chk("overview." + k, ro_desk[k] or 0, ro_port[k] or 0)

# 6) Category statistics
cs_desk = db.get_category_statistics()
cs_port = {r["category"]: r for r in S.compute_category_statistics(
    [{"category": t["category"], "amount": t["amount"], "fund_id": t["fund_id"], "txn_date": t["txn_date"]} for t in txns_all])}
chk("catstats_count", len(cs_desk), len(cs_port))
for r in cs_desk:
    p = cs_port.get(r["category"], {})
    for k in ("total", "count", "avg", "max", "share"):
        chk(f"catstat[{r['category']}].{k}", r[k], p.get(k, -1))

# 7) Fund flows
ff_desk = db.get_fund_flows()
ff_port = {r["id"]: r for r in S.compute_fund_flows(
    [{"id": f["id"], "name": f["name"]} for f in funds],
    [{"fund_id": t["fund_id"], "amount": t["amount"], "txn_date": t["txn_date"]} for t in txns_all])}
chk("flows_count", len(ff_desk), len(ff_port))
for r in ff_desk:
    p = ff_port.get(r["id"], {})
    for k in ("out_flow", "in_flow", "net", "count"):
        chk(f"flow[{r['name']}].{k}", r[k], p.get(k, -1))

print()
print("REAL-DATA PARITY:", "ALL MATCH" if mism == 0 else f"{mism} MISMATCHES")
