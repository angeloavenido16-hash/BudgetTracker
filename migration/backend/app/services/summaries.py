"""
app/services/summaries.py
─────────────────────────
⭐ ALL financial formulas, ported verbatim from the desktop app's database.py.

These are the "source of truth" calculations that took many iterations to get
right. The math here MUST stay identical to the desktop app. When wiring these
into async SQLAlchemy queries, keep the arithmetic exactly as written below and
verify against ../docs/PARITY_CHECKLIST.md.

The functions are written in a DB-agnostic way: they take plain Python
rows/dicts and return dicts. The router layer is responsible for fetching the
rows (via async SQLAlchemy) and passing them in. This makes the formulas unit-
testable without a database.
"""
from __future__ import annotations
from collections import defaultdict


# ── Category helpers ────────────────────────────────────────────────────────
def _is_savings(category: str) -> bool:
    return category.lower() == "savings"


def _is_carry_over(category: str) -> bool:
    return category.lower() in ("carry over", "carry_over")


def _is_house(category: str) -> bool:
    return category.lower() == "house"


# ════════════════════════════════════════════════════════════════════════════
# Per-fund summary  (was: database.get_fund_summary / get_all_fund_summaries)
# ════════════════════════════════════════════════════════════════════════════
def compute_fund_summary(income: float, txns: list[dict]) -> dict:
    """Mirror of the desktop per-fund summary.

    txns: list of {"category": str, "amount": float}

    Excel parity:
      Expenses  = SUM(all txn amounts)             (raw, like =SUM(sheet!B:B))
      Remaining = income - Expenses                (Excel Col D)
      Savings   = SUM(savings txns where amount > 0)
      CarryOver = SUM(carry-over txns where amount > 0)
      House     = SUM(house txns, BOTH signs)
    """
    total_expenses = sum(t["amount"] for t in txns)

    savings = sum(t["amount"] for t in txns
                  if _is_savings(t["category"]) and t["amount"] > 0)
    carry_over = sum(t["amount"] for t in txns
                     if _is_carry_over(t["category"]) and t["amount"] > 0)
    house = sum(t["amount"] for t in txns
                if _is_house(t["category"]))

    return {
        "income":     income,
        "expenses":   round(total_expenses, 2),
        "savings":    round(savings, 2),
        "house":      round(house, 2),
        "carry_over": round(carry_over, 2),
        "remaining":  round(income - total_expenses, 2),
    }


def compute_all_fund_summaries(
    funds: list[dict], txns: list[dict]
) -> dict[int, dict]:
    """Bulk version. funds: [{"id", "amount"}], txns: [{"fund_id","category","amount"}]."""
    by_fund: dict[int, list] = defaultdict(list)
    for t in txns:
        by_fund[t["fund_id"]].append(t)

    return {
        f["id"]: compute_fund_summary(f["amount"], by_fund[f["id"]])
        for f in funds
    }


# ════════════════════════════════════════════════════════════════════════════
# Dashboard totals  (was: database.get_dashboard_totals)
# ════════════════════════════════════════════════════════════════════════════
def compute_dashboard_totals(
    funds: list[dict], txns: list[dict], bpi_balance: float, year=None
) -> dict:
    """Mirror of the desktop dashboard.

    funds: [{"id", "fund_type", "amount", "cutoff_date"}]
    txns:  [{"fund_id", "amount", "txn_date"}]

    ``year`` ("YYYY") optionally scopes the figures: funds are kept when their
    cutoff_date falls in that year and transactions when their txn_date does.
    ``None`` = all-time (identical to the original behaviour / desktop parity).

    Rules (fund_type 'other' = special savings bucket):
      Total Income     = SUM(amount) for fund_type != 'other'
      Total Expenses   = SUM(txn.amount) joined to non-'other' funds
      Total Savings    = SUM(Remaining) of 'other' funds
                       = SUM(other.amount) - SUM(other txns)
      Net Remaining    = SUM(all funds.amount) - SUM(all txns)
      NonOtherRemaining= SUM(non-other amount) - SUM(non-other txns)
      Missing Expenses = bpi_balance - NonOtherRemaining   (computed in router/UI)
    """
    if year:
        funds = [f for f in funds if (f.get("cutoff_date") or "")[:4] == str(year)]
        txns = [t for t in txns if (t.get("txn_date") or "")[:4] == str(year)]

    other_ids     = {f["id"] for f in funds if f["fund_type"] == "other"}
    non_other_ids = {f["id"] for f in funds if f["fund_type"] != "other"}

    total_income = sum(f["amount"] for f in funds if f["fund_type"] != "other")
    other_income = sum(f["amount"] for f in funds if f["fund_type"] == "other")
    all_income   = sum(f["amount"] for f in funds)

    total_expenses = sum(t["amount"] for t in txns if t["fund_id"] in non_other_ids)
    other_txn      = sum(t["amount"] for t in txns if t["fund_id"] in other_ids)
    net_txn_flow   = sum(t["amount"] for t in txns)

    total_savings       = other_income - other_txn
    net_remaining       = all_income - net_txn_flow
    non_other_remaining = total_income - total_expenses
    missing_expenses    = bpi_balance - non_other_remaining

    return {
        "total_income":        round(total_income, 2),
        "total_expenses":      round(total_expenses, 2),
        "total_savings":       round(total_savings, 2),
        "net_remaining":       round(net_remaining, 2),
        "non_other_remaining": round(non_other_remaining, 2),
        "missing_expenses":    round(missing_expenses, 2),
        "bpi_balance":         round(bpi_balance, 2),
        "fund_count":          len(funds),
    }


# ════════════════════════════════════════════════════════════════════════════
# Transaction-view "Savings" card override (was: transactions_view logic)
# ════════════════════════════════════════════════════════════════════════════
def savings_card_value(fund_type: str, summary: dict) -> float:
    """For 'other' funds the Savings card shows House + Remaining;
    otherwise it shows the plain positive-savings total."""
    if fund_type == "other":
        return round(summary["house"] + summary["remaining"], 2)
    return summary["savings"]


# ════════════════════════════════════════════════════════════════════════════
# Shared transaction filter  (was: database._apply_txn_filters)
# ════════════════════════════════════════════════════════════════════════════
def _txn_matches(t: dict, year=None, month=None, fund_id=None) -> bool:
    """True if a transaction passes the optional Year / Month / Fund filters.

    - ``year``    matches the 4-digit year of ``txn_date`` ("YYYY").
    - ``month``   matches the 2-digit month of ``txn_date`` ("01".."12"),
                  independent of year, so it combines with the year filter.
    - ``fund_id`` restricts to a single fund.

    Mirrors the SQL in the desktop ``_apply_txn_filters`` (SUBSTR(txn_date,1,4)
    and SUBSTR(txn_date,6,2)).
    """
    d = t.get("txn_date") or ""
    if year and d[:4] != str(year):
        return False
    if month and d[5:7] != str(month).zfill(2):
        return False
    if fund_id and t.get("fund_id") != fund_id:
        return False
    return True


# ════════════════════════════════════════════════════════════════════════════
# Dashboard charts  (was: database.get_spending_over_time /
#                         get_expense_by_category / get_transaction_years)
# ════════════════════════════════════════════════════════════════════════════
def compute_spending_over_time(txns: list[dict], year=None) -> list[tuple]:
    """Monthly spending totals across ALL transactions, newest month last.

    - Months come from each transaction's ``txn_date`` ("YYYY-MM"), independent
      of the fund it sits under.
    - Only **positive** amounts count as spending; negatives are ignored.
    - Pass ``year`` ("YYYY") to restrict to a single year; ``None`` = all years.

    Returns ``[(month, total), …]`` sorted by month ascending.
    """
    buckets: dict[str, float] = defaultdict(float)
    for t in txns:
        d = t.get("txn_date")
        if not d or t["amount"] <= 0:
            continue
        if year and d[:4] != str(year):
            continue
        buckets[d[:7]] += t["amount"]
    return [(m, round(v, 2)) for m, v in sorted(buckets.items())]


def compute_expense_by_category(txns: list[dict], fund_id=None,
                                year=None) -> list[tuple]:
    """Spending grouped by category, largest first (positive amounts only).

    Optionally filter by ``fund_id`` and/or ``year``.  Returns
    ``[(category, total), …]`` sorted by total descending.
    """
    buckets: dict[str, float] = defaultdict(float)
    for t in txns:
        if t["amount"] <= 0:
            continue
        if fund_id and t.get("fund_id") != fund_id:
            continue
        if year and (t.get("txn_date") or "")[:4] != str(year):
            continue
        buckets[t["category"]] += t["amount"]
    return sorted(((c, round(v, 2)) for c, v in buckets.items()),
                  key=lambda kv: kv[1], reverse=True)


def compute_transaction_years(txns: list[dict]) -> list[str]:
    """Distinct years ("YYYY") present in transaction dates, newest first."""
    years = {(t.get("txn_date") or "")[:4] for t in txns if t.get("txn_date")}
    years.discard("")
    return sorted(years, reverse=True)


def compute_category_over_time(txns: list[dict], category: str,
                               year=None, sign=None) -> list[tuple]:
    """Monthly totals for ONE category, oldest month first.

    ``sign`` selects which rows count: ``"out"`` keeps positive amounts only
    (outflow / spending), ``"in"`` keeps negatives and reports them as
    positive magnitudes (inflow / credits), and ``None`` keeps every sign.
    Rows without a ``txn_date`` are grouped under "Undated" so a category that
    has entries never appears empty. Optional ``year`` ("YYYY") restricts to
    dated rows in that year. Returns ``[(month, total), …]``.
    """
    cat = (category or "").lower()
    buckets: dict[str, float] = defaultdict(float)
    undated = 0.0
    for t in txns:
        if t["category"].lower() != cat:
            continue
        amt = t["amount"]
        if sign == "out" and amt <= 0:
            continue
        if sign == "in":
            if amt >= 0:
                continue
            amt = -amt  # show inflow as a positive bar height
        d = t.get("txn_date")
        if not d:
            undated += amt
            continue
        if year and d[:4] != str(year):
            continue
        buckets[d[:7]] += amt
    rows = [(m, round(v, 2)) for m, v in sorted(buckets.items())]
    if undated and not year:
        rows.append(("Undated", round(undated, 2)))
    return rows


# ════════════════════════════════════════════════════════════════════════════
# Reports — statistical aggregates  (was: database.get_report_overview /
#                         get_category_statistics / get_fund_flows)
# ════════════════════════════════════════════════════════════════════════════
def compute_report_overview(txns: list[dict], year=None, fund_id=None,
                            month=None) -> dict:
    """Bundle of budget-management statistics for the Reports → Overview tab.

    ``txns`` rows should carry ``amount``, ``category``, ``txn_date`` and (for
    the "biggest expense" insight) ``fund_name``.  Spending = positive amounts
    only.  All figures honour the Year / Month / Fund filters.
    """
    spend = [t for t in txns
             if t["amount"] > 0 and _txn_matches(t, year, month, fund_id)]

    total_spent = round(sum(t["amount"] for t in spend), 2)
    txn_count   = len(spend)
    avg_txn     = round(total_spent / txn_count, 2) if txn_count else 0.0

    savings = round(sum(t["amount"] for t in spend
                        if _is_savings(t["category"])), 2)

    biggest = max(spend, key=lambda t: t["amount"]) if spend else None

    # Monthly breakdown
    monthly: dict[str, float] = defaultdict(float)
    for t in spend:
        d = t.get("txn_date") or ""
        if d:
            monthly[d[:7]] += t["amount"]
    months = [(m, round(v, 2)) for m, v in sorted(monthly.items())]

    active_months = len(months)
    avg_monthly   = round(total_spent / active_months, 2) if active_months else 0.0
    busiest       = max(months, key=lambda m: m[1]) if months else None
    quietest      = min(months, key=lambda m: m[1]) if months else None

    mom_change = None
    if len(months) >= 2 and months[-2][1]:
        mom_change = round((months[-1][1] - months[-2][1]) / months[-2][1] * 100, 2)

    # Category aggregates (for top / most frequent).  Mirror the desktop:
    # the rows are ordered by total DESC, and `most_frequent` is the first row
    # achieving the max count — so on a COUNT TIE the larger-total category wins.
    cat_total: dict[str, float] = defaultdict(float)
    cat_count: dict[str, int]   = defaultdict(int)
    for t in spend:
        cat_total[t["category"]] += t["amount"]
        cat_count[t["category"]] += 1
    cats = sorted(
        ((c, cat_total[c], cat_count[c]) for c in cat_total),
        key=lambda r: r[1], reverse=True,
    )

    top_category       = (cats[0][0], round(cats[0][1], 2)) if cats else None
    top_category_share = (round(cats[0][1] / total_spent * 100, 2)
                          if cats and total_spent else 0.0)
    # max() over the total-DESC list → first row with the highest count, exactly
    # like `max(cats, key=lambda r: r["cnt"])` in the desktop SQL result.
    most_frequent = max(cats, key=lambda r: r[2]) if cats else None

    return {
        "total_spent":        total_spent,
        "txn_count":          txn_count,
        "avg_txn":            avg_txn,
        "savings":            savings,
        "avg_monthly":        avg_monthly,
        "active_months":      active_months,
        "biggest": ({
            "amount":    round(biggest["amount"], 2),
            "category":  biggest["category"],
            "txn_date":  biggest.get("txn_date"),
            "fund_name": biggest.get("fund_name"),
        } if biggest else None),
        "busiest_month":      busiest,
        "quietest_month":     quietest,
        "mom_change":         mom_change,
        "latest_month":       months[-1] if months else None,
        "top_category":       top_category,
        "top_category_share": top_category_share,
        "most_frequent":      (most_frequent[0], most_frequent[2]) if most_frequent else None,
    }


def compute_category_statistics(txns: list[dict], year=None, fund_id=None,
                                month=None) -> list[dict]:
    """Per-category spend stats: total, count, average, max, % share.

    Spending only (positive amounts).  Sorted by total spent, descending.
    """
    spend = [t for t in txns
             if t["amount"] > 0 and _txn_matches(t, year, month, fund_id)]

    by_cat: dict[str, list] = defaultdict(list)
    for t in spend:
        by_cat[t["category"]].append(t["amount"])

    grand_total = sum(t["amount"] for t in spend) or 1.0

    rows = [
        {
            "category": cat,
            "total":    round(sum(amts), 2),
            "count":    len(amts),
            "avg":      round(sum(amts) / len(amts), 2),
            "max":      round(max(amts), 2),
            "share":    round(sum(amts) / grand_total * 100, 2),
        }
        for cat, amts in by_cat.items()
    ]
    rows.sort(key=lambda r: r["total"], reverse=True)
    return rows


def compute_fund_flows(funds: list[dict], txns: list[dict], year=None,
                       month=None) -> list[dict]:
    """Per-fund money flows for the Reports → 'Ins & Outs' tab.

    - **Out (−)** = money spent    = SUM(amount) where amount > 0
    - **In (+)**  = money returned = SUM(-amount) where amount < 0 (refunds)
    - **Net**     = In − Out       (negative = net spending)

    ``funds`` = ``[{"id","name"}, …]``.  Funds with no activity in the period
    are still included (with zero flows), mirroring the desktop LEFT JOIN.
    Sorted by Out descending.
    """
    flows = {
        f["id"]: {"id": f["id"], "name": f["name"],
                  "out_flow": 0.0, "in_flow": 0.0, "count": 0}
        for f in funds
    }
    for t in txns:
        fl = flows.get(t.get("fund_id"))
        if fl is None or not _txn_matches(t, year, month, None):
            continue
        fl["count"] += 1
        if t["amount"] > 0:
            fl["out_flow"] += t["amount"]
        elif t["amount"] < 0:
            fl["in_flow"] += -t["amount"]

    result = []
    for fl in flows.values():
        fl["out_flow"] = round(fl["out_flow"], 2)
        fl["in_flow"]  = round(fl["in_flow"], 2)
        fl["net"]      = round(fl["in_flow"] - fl["out_flow"], 2)
        result.append(fl)
    result.sort(key=lambda r: r["out_flow"], reverse=True)
    return result
