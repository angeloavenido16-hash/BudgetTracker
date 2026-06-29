"""
sanity_check.py  –  Automated end-to-end sanity check for Budget Tracker.

Exercises the data layer, every view, all refresh paths, navigation, mask
toggles, pagination, sorting, filters, and a full CRUD round-trip — then a
clean shutdown.  Prints a PASS/FAIL summary.  Makes NO permanent data changes
(any rows it creates, it deletes).

Run:  python sanity_check.py
"""
import time
import traceback

import customtkinter as ctk

import database as db
import app as app_module


# ── tiny test harness ───────────────────────────────────────────────────────
_results = []

def check(name, fn):
    t0 = time.perf_counter()
    try:
        fn()
        dt = (time.perf_counter() - t0) * 1000
        _results.append((name, True, f"{dt:6.1f} ms", ""))
    except Exception as e:  # noqa: BLE001
        dt = (time.perf_counter() - t0) * 1000
        _results.append((name, False, f"{dt:6.1f} ms", repr(e)))
        traceback.print_exc()


def section(title):
    _results.append((f"── {title} ", None, "", ""))


# ════════════════════════════════════════════════════════════════════════════
# 1. DATA LAYER
# ════════════════════════════════════════════════════════════════════════════
def test_data_layer():
    section("DATA LAYER")

    check("initialize_db (idempotent)", db.initialize_db)

    def funds():
        fs = db.get_funds()
        assert isinstance(fs, list)
        if fs:
            assert "id" in fs[0] and "fund_type" in fs[0]
    check("get_funds", funds)

    def summaries():
        s = db.get_all_fund_summaries()
        assert isinstance(s, dict)
        for v in s.values():
            assert {"income", "expenses", "savings", "house",
                    "carry_over", "remaining"} <= set(v)
    check("get_all_fund_summaries (bulk)", summaries)

    def per_fund_matches_bulk():
        bulk = db.get_all_fund_summaries()
        for fid, bsum in list(bulk.items())[:5]:
            single = db.get_fund_summary(fid)
            for k in ("income", "expenses", "remaining"):
                assert abs(single[k] - bsum[k]) < 0.01, f"{k} mismatch fund {fid}"
    check("get_fund_summary == bulk (parity)", per_fund_matches_bulk)

    def dash():
        d = db.get_dashboard_totals()
        assert {"total_income", "total_expenses", "total_savings",
                "net_remaining", "non_other_remaining", "fund_count"} <= set(d)
    check("get_dashboard_totals", dash)

    check("get_transactions (all)", lambda: db.get_transactions())
    check("get_categories", lambda: db.get_categories())
    check("get_transaction_years", lambda: db.get_transaction_years())
    check("get_latest_bpi_balance", lambda: db.get_latest_bpi_balance())
    check("get_spending_over_time", lambda: db.get_spending_over_time())
    check("get_expense_by_category", lambda: db.get_expense_by_category())

    # Reports stats with combined filters
    def reports_stats():
        yrs = db.get_transaction_years()
        yr = yrs[0] if yrs else None
        o = db.get_report_overview(year=yr, month="07")
        assert "total_spent" in o and "txn_count" in o
        cs = db.get_category_statistics(year=yr)
        assert isinstance(cs, list)
        fl = db.get_fund_flows(year=yr, month="07")
        assert isinstance(fl, list)
    check("report_overview / category_stats / fund_flows", reports_stats)


# ════════════════════════════════════════════════════════════════════════════
# 2. CRUD ROUND-TRIP  (creates + cleans up its own data)
# ════════════════════════════════════════════════════════════════════════════
def test_crud_roundtrip():
    section("CRUD ROUND-TRIP (self-cleaning)")

    state = {}

    def add_fund():
        fid = db.add_fund("__SANITY_FUND__", "other", 1000.0,
                          cutoff_date="2026-06-15", notes="sanity")
        state["fid"] = fid
        assert db.get_fund_by_id(fid)["name"] == "__SANITY_FUND__"
    check("add_fund", add_fund)

    def update_fund():
        db.update_fund(state["fid"], "__SANITY_FUND__", "other", 2000.0,
                       cutoff_date="2026-06-15", notes="sanity-edited")
        assert db.get_fund_by_id(state["fid"])["amount"] == 2000.0
    check("update_fund", update_fund)

    def add_txn():
        tid = db.add_transaction(state["fid"], "Savings", 300.0,
                                 txn_date="2026-06-20", remarks="sanity")
        state["tid"] = tid
        summ = db.get_fund_summary(state["fid"])
        assert summ["savings"] == 300.0
        assert summ["remaining"] == 2000.0 - 300.0
    check("add_transaction + summary recompute", add_txn)

    def update_txn():
        db.update_transaction(state["tid"], "Savings", 500.0,
                              txn_date="2026-06-20", remarks="sanity2")
        assert db.get_fund_summary(state["fid"])["savings"] == 500.0
    check("update_transaction", update_txn)

    def delete_txn():
        db.delete_transaction(state["tid"])
        assert db.get_fund_summary(state["fid"])["expenses"] == 0
    check("delete_transaction", delete_txn)

    def cascade_delete_fund():
        # add a txn then delete the fund — txn should cascade away
        tid = db.add_transaction(state["fid"], "House", 50.0, txn_date="2026-06-21")
        db.delete_fund(state["fid"])
        assert db.get_fund_by_id(state["fid"]) is None
        assert all(t["id"] != tid for t in db.get_transactions())
    check("delete_fund (cascade transactions)", cascade_delete_fund)

    def category_roundtrip():
        before = set(db.get_categories())
        db.add_category("__SANITY_CAT__")
        assert "__SANITY_CAT__" in db.get_categories()
        db.delete_category("__SANITY_CAT__")
        assert set(db.get_categories()) == before
    check("add/delete category (no side effects)", category_roundtrip)

    def bpi_roundtrip():
        original = db.get_latest_bpi_balance()
        db.update_bpi_balance(99999.99)
        assert abs(db.get_latest_bpi_balance() - 99999.99) < 0.01
        db.update_bpi_balance(original)  # restore
    check("update_bpi_balance (restored)", bpi_roundtrip)


# ════════════════════════════════════════════════════════════════════════════
# 3. FULL APP — views, refreshes, navigation, runtime
# ════════════════════════════════════════════════════════════════════════════
def test_app_runtime():
    section("APP RUNTIME (views / refresh / nav)")

    state = {}

    def boot():
        a = app_module.BudgetTrackerApp()
        a.update()
        state["app"] = a
        # all 5 views built?
        assert set(a._views) == {"dashboard", "funds", "transactions",
                                 "reports", "settings"}
    check("app boots + builds all 5 views", boot)

    a = state["app"]

    def nav_all():
        for key in ("dashboard", "funds", "transactions", "reports", "settings"):
            a._show_view(key)
            a.update()
            assert a._current_view_key == key
    check("navigate to every view", nav_all)

    def dashboard_refresh():
        a._show_view("dashboard")
        a._dashboard_view.refresh()
        a.update()
    check("dashboard.refresh()", dashboard_refresh)

    def dashboard_year_filter():
        dv = a._dashboard_view
        yrs = db.get_transaction_years()
        if yrs:
            dv._on_year_changed(yrs[0]); a.update()
            dv._on_year_changed("All");  a.update()
    check("dashboard year filter -> charts redraw", dashboard_year_filter)

    def funds_refresh_mask_page_sort():
        a._show_view("funds")
        fv = a._funds_view
        fv.refresh(); a.update()
        fv._toggle_mask(); a.update()       # mask on/off
        fv._toggle_mask(); a.update()
        fv._next_page(); a.update()         # pagination
        fv._prev_page(); a.update()
        fv._on_header_click(3); a.update()  # sort by Amount
        fv._on_header_click(3); a.update()  # toggle direction
    check("funds refresh/mask/page/sort", funds_refresh_mask_page_sort)

    def reports_tabs_and_filters():
        a._show_view("reports")
        rv = a._reports_view
        for tab in ("overview", "category", "flows", "overview"):
            rv._switch_tab(tab); a.update()
            assert len(rv.body.winfo_children()) > 0, f"empty body on {tab}"
        yrs = db.get_transaction_years()
        if yrs:
            rv._on_year_changed(yrs[0]); a.update()
        rv._on_month_changed("July"); a.update()
        rv._on_month_changed("All");  a.update()
    check("reports: all tabs render + year/month filters", reports_tabs_and_filters)

    def settings_renders():
        a._show_view("settings")
        sv = a._settings_view
        assert sv.lbl_bpi_current.cget("text").startswith("₱")
        a.update()
        # Categories now paginate + search — exercise both.
        all_cats = db.get_categories()
        sv._load_cats(); a.update()
        # At most one page worth of chips should be rendered at a time.
        assert len(sv._cat_page_items) <= sv._cat_page_size
        if len(all_cats) > sv._cat_page_size:
            sv._cat_next_page(); a.update()
            assert sv._cat_page == 1, "next page should advance"
            sv._cat_prev_page(); a.update()
            assert sv._cat_page == 0, "prev page should go back"
        # Search narrows the list and resets to page 1.
        if all_cats:
            sv._cat_search_var.set(all_cats[0][:2]); a.update()
            assert sv._cat_page == 0
            assert all(all_cats[0][:2].lower() in c.lower()
                       for c in sv._filtered_cats()), "search must filter"
            sv._cat_search_var.set(""); a.update()   # clear
    check("settings: BPI card + category search/paging", settings_renders)

    def fund_to_txn_navigation():
        funds = db.get_funds()
        if funds:
            fid = funds[0]["id"]
            a._open_fund_transactions(fid)
            a.update()
            assert a._current_view_key == "transactions"
            assert a._transactions_view._fund_id == fid
    check("fund -> transactions deep-link", fund_to_txn_navigation)

    def lazy_stale_refresh():
        # Simulate data change while on dashboard; others marked stale & refresh on visit
        a._show_view("dashboard")
        a._on_data_changed()
        assert {"funds", "transactions", "reports"} <= a._stale_views
        a._show_view("funds")          # visiting clears its stale flag
        a.update()
        assert "funds" not in a._stale_views
    check("lazy stale-refresh bookkeeping", lazy_stale_refresh)

    def rapid_nav_stress():
        order = ["dashboard", "funds", "reports", "transactions",
                 "settings", "reports", "dashboard", "funds"]
        for _ in range(6):
            for k in order:
                a._show_view(k)
            a.update()
    check("rapid navigation stress (48 switches)", rapid_nav_stress)

    def clean_shutdown():
        a.destroy()
    check("clean shutdown (destroy)", clean_shutdown)


# ════════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.perf_counter()
    test_data_layer()
    test_crud_roundtrip()
    test_app_runtime()
    total = time.perf_counter() - t0

    print("\n" + "=" * 68)
    print("  BUDGET TRACKER — SANITY CHECK RESULTS")
    print("=" * 68)
    passed = failed = 0
    for name, ok, dt, err in _results:
        if ok is None:
            print(f"\n{name}{'─' * (50 - len(name))}")
            continue
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name:<46} {dt}")
        if err:
            print(f"         ↳ {err}")
        passed += ok
        failed += (not ok)
    print("=" * 68)
    print(f"  {passed} passed, {failed} failed   |   total {total:.2f}s")
    print("=" * 68)
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
