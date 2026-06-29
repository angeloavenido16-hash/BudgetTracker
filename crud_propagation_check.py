"""
crud_propagation_check.py  –  Does ADD / EDIT / DELETE update EVERYTHING?

This probe answers two questions for funds *and* transactions:

  1. PROPAGATION — when you add / edit / delete, do ALL views update?
     We read the **actual on-screen widget text** (Dashboard cards, the
     Transactions Remaining card) plus each view's re-queried data, before and
     after every operation, and assert the numbers move exactly as expected and
     fully revert on delete.

  2. RUNTIME — how long does "update everything" take?  For each operation we
     time the complete cycle: the DB write, the active view's immediate refresh,
     and a navigation sweep that forces every other (now-stale) view to rebuild.

It drives the real view code paths (the same calls each view makes the moment a
dialog is saved), so it tests the live propagation machinery — not just the DB.
All data it creates, it deletes; the database is left exactly as it was.

Run:  python crud_propagation_check.py
"""
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")   # peso sign / arrows safe in console
except Exception:
    pass

import database as db
import app as app_module


PROBE_FUND_NAME = "__CRUD_PROBE_FUND__"
PROBE_INCOME    = 10_000.0
TODAY           = "2026-06-29"

_fail = 0


# ── helpers ──────────────────────────────────────────────────────────────────
def money(text: str) -> float:
    """Parse '₱1,234.56' / '-₱20.00' / '+₱5' → float."""
    t = (text or "").replace("₱", "").replace(",", "").replace(" ", "")
    t = t.replace("−", "-")          # unicode minus → ascii
    t = t.replace("+", "")
    try:
        return float(t)
    except ValueError:
        return float("nan")


def approx(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(a - b) <= tol


def ok(label, condition, detail=""):
    global _fail
    tag = "PASS" if condition else "FAIL"
    if not condition:
        _fail += 1
    print(f"   [{tag}] {label}" + (f"   {detail}" if detail else ""))


def sweep(a):
    """Force every data view to be current (refreshes any stale views)."""
    for k in ("dashboard", "funds", "reports", "transactions"):
        a._show_view(k)
    a.update()


def snapshot(a, fid):
    """Read displayed/derived values across ALL views after a full refresh sweep.

    Returns a dict mixing real widget text (UI proof) and re-queried numbers.
    """
    # Dashboard — cards are unmasked; read the live widget text
    a._show_view("dashboard")
    a._dashboard_view.refresh()
    a.update()
    dv = a._dashboard_view
    dash_expenses = money(dv.card_expenses.lbl_value.cget("text"))
    dash_net      = money(dv.card_net.lbl_value.cget("text"))

    # Funds — re-query through the view, read the probe fund's cached Remaining
    a._show_view("funds")
    a._funds_view.refresh()
    a.update()
    fv = a._funds_view
    fund_remaining = None
    for f, summ in fv._pairs_cache:
        if f["id"] == fid:
            fund_remaining = round(summ.get("remaining", 0), 2)
            break

    # Transactions — load probe fund, unmask, read the live card text
    a._transactions_view.load_fund(fid)
    a._transactions_view._masked = False
    a._transactions_view._refresh_summary_cards()
    a.update()
    tv = a._transactions_view
    txn_expenses  = money(tv.card_expenses.lbl_value.cget("text"))
    txn_remaining = money(tv.card_remaining.lbl_value.cget("text"))
    txn_count     = len(tv._txn_rows)

    # Reports — overview total across all funds/years
    rep_total = db.get_report_overview()["total_spent"]

    return {
        "dash_expenses":  dash_expenses,
        "dash_net":       dash_net,
        "fund_remaining": fund_remaining,
        "txn_expenses":   txn_expenses,
        "txn_remaining":  txn_remaining,
        "txn_count":      txn_count,
        "rep_total":      rep_total,
    }


def timed_txn_op(a, fn, fid):
    """Run a transaction CRUD op the way TransactionsView does, timing the
    FULL 'update everything' cycle: write -> active refresh -> stale sweep."""
    a._open_fund_transactions(fid)     # make Transactions the active view
    a.update()
    t0 = time.perf_counter()
    fn()                                # the db write (what the dialog does)
    a._transactions_view._load_transactions()   # what _add/_edit/_delete does
    a._on_data_changed()                # marks others stale + refreshes active
    sweep(a)                            # force every stale view to rebuild
    return (time.perf_counter() - t0) * 1000


def timed_fund_op(a, fn):
    """Run a fund CRUD op the way FundsView does, timing the full cycle."""
    a._show_view("funds")
    a.update()
    t0 = time.perf_counter()
    fn()
    a._funds_view.refresh()
    a._on_data_changed()
    sweep(a)
    return (time.perf_counter() - t0) * 1000


# ════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  CRUD PROPAGATION + RUNTIME CHECK")
    print("=" * 70)

    db.initialize_db()

    # Make sure a 'Food' category exists (restore later if we add it)
    cats_before = set(db.get_categories())
    if "Food" not in cats_before:
        db.add_category("Food")
    added_food = "Food" not in cats_before

    a = app_module.BudgetTrackerApp()
    a.update()

    timings = {}
    try:
        # ── Create a dedicated probe fund (salary => counts on Dashboard) ──
        fid = db.add_fund(PROBE_FUND_NAME, "salary", PROBE_INCOME,
                          cutoff_date=TODAY, notes="crud probe")
        a._on_data_changed()
        sweep(a)
        base = snapshot(a, fid)
        print(f"\n  Probe fund #{fid} created (income ₱{PROBE_INCOME:,.0f}, 0 txns)")
        print(f"  Baseline: dash_expenses=₱{base['dash_expenses']:,.2f}  "
              f"dash_net=₱{base['dash_net']:,.2f}  "
              f"fund_remaining=₱{base['fund_remaining']:,.2f}  "
              f"reports_total=₱{base['rep_total']:,.2f}")
        ok("probe fund starts with 0 transactions", base["txn_count"] == 0)
        ok("probe fund Remaining == full income",
           approx(base["fund_remaining"], PROBE_INCOME),
           f"₱{base['fund_remaining']:,.2f}")

        # ─────────────────────────────────────────────────────────────────
        # ADD a transaction (Food, ₱1,500)
        # ─────────────────────────────────────────────────────────────────
        print("\n── ADD transaction  (Food ₱1,500) ─────────────────────────")
        state = {}
        def do_add():
            state["tid"] = db.add_transaction(fid, "Food", 1500.0,
                                              txn_date=TODAY, remarks="probe")
        timings["txn add"] = timed_txn_op(a, do_add, fid)
        after = snapshot(a, fid)

        ok("Transactions: count went 0 → 1", after["txn_count"] == 1)
        ok("Transactions card Remaining = income − 1500",
           approx(after["txn_remaining"], PROBE_INCOME - 1500),
           f"₱{after['txn_remaining']:,.2f}")
        ok("Transactions card Expenses = 1500",
           approx(after["txn_expenses"], 1500.0),
           f"₱{after['txn_expenses']:,.2f}")
        ok("Dashboard Total Expenses +1500",
           approx(after["dash_expenses"], base["dash_expenses"] + 1500),
           f"₱{after['dash_expenses']:,.2f}")
        ok("Dashboard Net Remaining −1500",
           approx(after["dash_net"], base["dash_net"] - 1500),
           f"₱{after['dash_net']:,.2f}")
        ok("Funds view Remaining −1500",
           approx(after["fund_remaining"], base["fund_remaining"] - 1500),
           f"₱{after['fund_remaining']:,.2f}")
        ok("Reports total spent +1500",
           approx(after["rep_total"], base["rep_total"] + 1500),
           f"₱{after['rep_total']:,.2f}")

        # ─────────────────────────────────────────────────────────────────
        # EDIT the transaction (1500 → 2222)
        # ─────────────────────────────────────────────────────────────────
        print("\n── EDIT transaction  (₱1,500 → ₱2,222) ────────────────────")
        def do_edit():
            db.update_transaction(state["tid"], "Food", 2222.0,
                                  txn_date=TODAY, remarks="probe-edit")
        timings["txn edit"] = timed_txn_op(a, do_edit, fid)
        after = snapshot(a, fid)

        ok("Transactions card Remaining = income − 2222",
           approx(after["txn_remaining"], PROBE_INCOME - 2222),
           f"₱{after['txn_remaining']:,.2f}")
        ok("Dashboard Total Expenses = base +2222",
           approx(after["dash_expenses"], base["dash_expenses"] + 2222),
           f"₱{after['dash_expenses']:,.2f}")
        ok("Funds view Remaining = base −2222",
           approx(after["fund_remaining"], base["fund_remaining"] - 2222),
           f"₱{after['fund_remaining']:,.2f}")
        ok("Reports total spent = base +2222",
           approx(after["rep_total"], base["rep_total"] + 2222),
           f"₱{after['rep_total']:,.2f}")

        # ─────────────────────────────────────────────────────────────────
        # DELETE the transaction → everything reverts to baseline
        # ─────────────────────────────────────────────────────────────────
        print("\n── DELETE transaction  → revert to baseline ───────────────")
        def do_del():
            db.delete_transaction(state["tid"])
        timings["txn delete"] = timed_txn_op(a, do_del, fid)
        after = snapshot(a, fid)

        ok("Transactions: count back to 0", after["txn_count"] == 0)
        ok("Transactions card Remaining back to full income",
           approx(after["txn_remaining"], PROBE_INCOME),
           f"₱{after['txn_remaining']:,.2f}")
        ok("Dashboard Total Expenses back to baseline",
           approx(after["dash_expenses"], base["dash_expenses"]),
           f"₱{after['dash_expenses']:,.2f}")
        ok("Dashboard Net Remaining back to baseline",
           approx(after["dash_net"], base["dash_net"]),
           f"₱{after['dash_net']:,.2f}")
        ok("Funds view Remaining back to baseline",
           approx(after["fund_remaining"], base["fund_remaining"]),
           f"₱{after['fund_remaining']:,.2f}")
        ok("Reports total spent back to baseline",
           approx(after["rep_total"], base["rep_total"]),
           f"₱{after['rep_total']:,.2f}")

        # ─────────────────────────────────────────────────────────────────
        # FUND edit + delete propagation (income drives Dashboard + Net)
        # ─────────────────────────────────────────────────────────────────
        print("\n── EDIT fund  (income ₱10,000 → ₱12,500) ──────────────────")
        def do_fund_edit():
            db.update_fund(fid, PROBE_FUND_NAME, "salary", 12_500.0,
                           cutoff_date=TODAY, notes="probe")
        timings["fund edit"] = timed_fund_op(a, do_fund_edit)
        after = snapshot(a, fid)
        ok("Funds view Remaining reflects new income (12,500)",
           approx(after["fund_remaining"], 12_500.0),
           f"₱{after['fund_remaining']:,.2f}")
        ok("Dashboard Net Remaining +2500 vs baseline",
           approx(after["dash_net"], base["dash_net"] + 2500),
           f"₱{after['dash_net']:,.2f}")

        print("\n── DELETE fund  → removed from every view ─────────────────")
        def do_fund_del():
            db.delete_fund(fid)
        timings["fund delete"] = timed_fund_op(a, do_fund_del)
        a.update()
        gone_funds = all(f["id"] != fid for f in db.get_funds())
        final = {
            "dash_expenses": money(a._dashboard_view.card_expenses.lbl_value.cget("text")),
            "dash_net":      money(a._dashboard_view.card_net.lbl_value.cget("text")),
            "rep_total":     db.get_report_overview()["total_spent"],
        }
        a._show_view("funds"); a._funds_view.refresh(); a.update()
        in_cache = any(f["id"] == fid for f, _ in a._funds_view._pairs_cache)
        ok("probe fund removed from DB", gone_funds)
        ok("probe fund removed from Funds view cache", not in_cache)
        # The probe fund had 0 transactions at delete time, so deleting it pulls
        # its full income back out of Net Remaining: expect base − PROBE_INCOME.
        ok("Dashboard Net Remaining drops by the deleted fund's income",
           approx(final["dash_net"], base["dash_net"] - PROBE_INCOME),
           f"₱{final['dash_net']:,.2f}  (expected ₱{base['dash_net'] - PROBE_INCOME:,.2f})")
        ok("Reports total unchanged (deleted fund had no spending)",
           approx(final["rep_total"], base["rep_total"]),
           f"₱{final['rep_total']:,.2f}")

    finally:
        # Cleanup safety net — make sure nothing of ours survives
        for f in db.get_funds():
            if f["name"] == PROBE_FUND_NAME:
                db.delete_fund(f["id"])
        if added_food:
            db.delete_category("Food")
        try:
            a.destroy()
        except Exception:
            pass

    # ── runtime table ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RUNTIME  —  full 'update everything' cycle per operation")
    print("  (DB write + active-view refresh + sweep of all other views)")
    print("-" * 70)
    for label in ("txn add", "txn edit", "txn delete",
                  "fund edit", "fund delete"):
        if label in timings:
            print(f"   {label:<14} {timings[label]:8.1f} ms")
    print("=" * 70)
    print(f"  RESULT: {'ALL PROPAGATION CHECKS PASSED' if _fail == 0 else str(_fail) + ' CHECK(S) FAILED'}")
    print("=" * 70)
    return _fail


if __name__ == "__main__":
    raise SystemExit(main())
