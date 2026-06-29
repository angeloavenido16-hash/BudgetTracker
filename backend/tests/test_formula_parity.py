"""
tests/test_formula_parity.py
────────────────────────────
Locks in the financial formulas so the web API can never silently drift from
the desktop app. Run:  pytest

These expected values are derived directly from the desktop app's rules
(see ../docs/FORMULAS.md). If a test here fails, the math changed — STOP and
compare against the desktop app before editing.
"""
from app.services.summaries import (
    compute_fund_summary,
    compute_all_fund_summaries,
    compute_dashboard_totals,
    savings_card_value,
    compute_spending_over_time,
    compute_expense_by_category,
    compute_transaction_years,
    compute_report_overview,
    compute_category_statistics,
    compute_fund_flows,
)


# ── Per-fund summary ────────────────────────────────────────────────────────
def test_fund_summary_basic():
    txns = [
        {"category": "Groceries",  "amount": 1000},
        {"category": "Savings",    "amount": 500},
        {"category": "Savings",    "amount": -200},   # negative ignored for savings card
        {"category": "House",      "amount": 300},
        {"category": "House",      "amount": -100},    # house counts both signs
        {"category": "Carry Over", "amount": 250},
        {"category": "Carry Over", "amount": -50},     # negative ignored for carry-over
    ]
    s = compute_fund_summary(income=5000, txns=txns)

    assert s["expenses"]   == 1700           # raw sum of ALL amounts
    assert s["savings"]    == 500            # only positive savings
    assert s["house"]      == 200            # 300 + (-100)
    assert s["carry_over"] == 250            # only positive carry-over
    assert s["remaining"]  == 3300           # 5000 - 1700


def test_fund_summary_empty():
    s = compute_fund_summary(income=1000, txns=[])
    assert s == {
        "income": 1000, "expenses": 0, "savings": 0,
        "house": 0, "carry_over": 0, "remaining": 1000,
    }


def test_all_fund_summaries_grouping():
    funds = [{"id": 1, "amount": 1000}, {"id": 2, "amount": 2000}]
    txns = [
        {"fund_id": 1, "category": "Food",    "amount": 100},
        {"fund_id": 2, "category": "Savings", "amount": 400},
    ]
    out = compute_all_fund_summaries(funds, txns)
    assert out[1]["remaining"] == 900
    assert out[2]["remaining"] == 1600
    assert out[2]["savings"]   == 400


# ── Dashboard totals ────────────────────────────────────────────────────────
def test_dashboard_totals():
    funds = [
        {"id": 1, "fund_type": "salary", "amount": 10000},
        {"id": 2, "fund_type": "bonus",  "amount": 5000},
        {"id": 3, "fund_type": "other",  "amount": 8000},   # special savings bucket
    ]
    txns = [
        {"fund_id": 1, "amount": 4000},
        {"fund_id": 2, "amount": 1000},
        {"fund_id": 3, "amount": 3000},
    ]
    d = compute_dashboard_totals(funds, txns, bpi_balance=12000)

    assert d["total_income"]        == 15000   # salary + bonus (exclude 'other')
    assert d["total_expenses"]      == 5000    # txns on non-other funds (4000+1000)
    assert d["total_savings"]       == 5000    # other remaining: 8000 - 3000
    assert d["net_remaining"]       == 15000   # 23000 - 8000
    assert d["non_other_remaining"] == 10000   # 15000 - 5000
    assert d["missing_expenses"]    == 2000    # 12000 - 10000


# ── Savings card override for 'other' funds ─────────────────────────────────
def test_savings_card_override():
    summary = {"savings": 100, "house": 700, "remaining": 300}
    assert savings_card_value("other",  summary) == 1000   # house + remaining
    assert savings_card_value("salary", summary) == 100    # plain savings


# ════════════════════════════════════════════════════════════════════════════
# Dashboard charts — spending over time / by category / years
# ════════════════════════════════════════════════════════════════════════════
def test_spending_over_time_positive_only_by_month():
    txns = [
        {"txn_date": "2025-01-05", "amount": 100},
        {"txn_date": "2025-01-20", "amount": 50},
        {"txn_date": "2025-02-10", "amount": 200},
        {"txn_date": "2025-02-11", "amount": -80},   # negative ignored
        {"txn_date": "2026-03-01", "amount": 300},
        {"txn_date": None,          "amount": 999},   # no date ignored
    ]
    assert compute_spending_over_time(txns) == [
        ("2025-01", 150), ("2025-02", 200), ("2026-03", 300),
    ]
    # Year filter restricts to a single year
    assert compute_spending_over_time(txns, year="2025") == [
        ("2025-01", 150), ("2025-02", 200),
    ]


def test_expense_by_category_sorted_desc_positive_only():
    txns = [
        {"category": "Food",  "amount": 100, "fund_id": 1, "txn_date": "2025-01-01"},
        {"category": "Food",  "amount": 50,  "fund_id": 2, "txn_date": "2025-01-02"},
        {"category": "Rent",  "amount": 500, "fund_id": 1, "txn_date": "2025-01-03"},
        {"category": "Food",  "amount": -20, "fund_id": 1, "txn_date": "2025-01-04"},  # ignored
    ]
    assert compute_expense_by_category(txns) == [("Rent", 500), ("Food", 150)]
    # fund filter
    assert compute_expense_by_category(txns, fund_id=2) == [("Food", 50)]
    # year filter
    assert compute_expense_by_category(txns, year="2024") == []


def test_transaction_years_newest_first():
    txns = [
        {"txn_date": "2024-05-01"}, {"txn_date": "2026-01-01"},
        {"txn_date": "2025-09-09"}, {"txn_date": "2025-01-01"},
        {"txn_date": None}, {"txn_date": ""},
    ]
    assert compute_transaction_years(txns) == ["2026", "2025", "2024"]


# ════════════════════════════════════════════════════════════════════════════
# Reports — overview / category stats / fund flows
# ════════════════════════════════════════════════════════════════════════════
def _report_txns():
    return [
        {"fund_id": 1, "fund_name": "Salary", "category": "Food",
         "amount": 100, "txn_date": "2025-01-10"},
        {"fund_id": 1, "fund_name": "Salary", "category": "Food",
         "amount": 300, "txn_date": "2025-02-15"},
        {"fund_id": 1, "fund_name": "Salary", "category": "Rent",
         "amount": 600, "txn_date": "2025-02-01"},
        {"fund_id": 2, "fund_name": "Other",  "category": "Savings",
         "amount": 200, "txn_date": "2025-01-20"},
        {"fund_id": 2, "fund_name": "Other",  "category": "Food",
         "amount": -40, "txn_date": "2025-02-05"},   # refund (negative)
    ]


def test_report_overview_core_stats():
    o = compute_report_overview(_report_txns())
    # Spending = positive amounts only: 100+300+600+200 = 1200
    assert o["total_spent"] == 1200
    assert o["txn_count"]   == 4
    assert o["avg_txn"]     == 300
    assert o["savings"]     == 200                       # positive 'savings'
    # Two active months: Jan (100+200=300), Feb (300+600=900)
    assert o["active_months"] == 2
    assert o["avg_monthly"]   == 600                     # 1200 / 2
    assert o["busiest_month"]  == ("2025-02", 900)
    assert o["quietest_month"] == ("2025-01", 300)
    assert o["biggest"]["amount"]   == 600
    assert o["biggest"]["category"] == "Rent"
    assert o["biggest"]["fund_name"] == "Salary"
    assert o["top_category"] == ("Rent", 600)
    assert o["top_category_share"] == 50.0               # 600 / 1200
    assert o["most_frequent"] == ("Food", 2)             # Food appears twice (positive)
    # Month-over-month: Feb vs Jan = (900-300)/300 = 200%
    assert o["mom_change"] == 200.0
    assert o["latest_month"] == ("2025-02", 900)


def test_report_overview_filters():
    txns = _report_txns()
    jan = compute_report_overview(txns, month="01")
    assert jan["total_spent"] == 300                     # 100 + 200
    f1 = compute_report_overview(txns, fund_id=1)
    assert f1["total_spent"] == 1000                     # 100+300+600
    assert f1["savings"] == 0


def test_report_overview_most_frequent_tiebreak_prefers_higher_total():
    # Two categories each appear twice (a COUNT tie). The desktop orders by
    # total DESC and takes the first max-count row, so the bigger-total
    # category ("Rent") must win the tie over "Food".
    txns = [
        {"category": "Food", "amount": 10, "txn_date": "2025-01-01"},
        {"category": "Food", "amount": 10, "txn_date": "2025-01-02"},
        {"category": "Rent", "amount": 500, "txn_date": "2025-01-03"},
        {"category": "Rent", "amount": 500, "txn_date": "2025-01-04"},
    ]
    o = compute_report_overview(txns)
    assert o["most_frequent"] == ("Rent", 2)


def test_category_statistics_shares_and_max():
    rows = compute_category_statistics(_report_txns())
    by = {r["category"]: r for r in rows}
    # Rent: one txn of 600
    assert by["Rent"]["total"] == 600
    assert by["Rent"]["count"] == 1
    assert by["Rent"]["max"]   == 600
    # Food: 100 + 300 = 400 over 2 txns, avg 200, max 300
    assert by["Food"]["total"] == 400
    assert by["Food"]["count"] == 2
    assert by["Food"]["avg"]   == 200
    assert by["Food"]["max"]   == 300
    # Shares sum to 100 across all positive spend (1200): Rent 50, Food 33.33, Savings 16.67
    assert round(sum(r["share"] for r in rows)) == 100
    # Sorted by total desc
    assert [r["category"] for r in rows][0] == "Rent"


def test_fund_flows_in_out_net():
    funds = [{"id": 1, "name": "Salary"}, {"id": 2, "name": "Other"},
             {"id": 3, "name": "Idle"}]
    flows = compute_fund_flows(funds, _report_txns())
    by = {f["name"]: f for f in flows}
    # Salary: out = 100+300+600 = 1000, in = 0, net = -1000, count 3
    assert by["Salary"]["out_flow"] == 1000
    assert by["Salary"]["in_flow"]  == 0
    assert by["Salary"]["net"]      == -1000
    assert by["Salary"]["count"]    == 3
    # Other: out = 200, in = 40 (refund), net = -160, count 2
    assert by["Other"]["out_flow"] == 200
    assert by["Other"]["in_flow"]  == 40
    assert by["Other"]["net"]      == -160
    assert by["Other"]["count"]    == 2
    # Idle fund with no activity still listed, zeroed
    assert by["Idle"]["count"] == 0
    assert by["Idle"]["net"]   == 0
    # Sorted by out_flow desc → Salary first
    assert flows[0]["name"] == "Salary"
