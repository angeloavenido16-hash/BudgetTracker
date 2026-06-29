"""
app.py  –  Main entry point for the Budget Tracker desktop app.
Run:  python app.py
"""
import os
import customtkinter as ctk

import database as db
from widgets import COLORS, NavButton

# ── Views ────────────────────────────────────────────────────────────────
from views.dashboard       import DashboardView
from views.funds_view       import FundsView
from views.transactions_view import TransactionsView
from views.reports_view     import ReportsView
from views.settings_view    import SettingsView


# ── App appearance ────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BudgetTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Budget Tracker")
        self.geometry("1480x800")
        self.minsize(1200, 650)
        self.configure(fg_color=COLORS["bg"])

        # icon (optional – skip if file missing)
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self._current_fund_id: int | None = None
        self._current_view_key: str = "dashboard"
        self._stale_views: set[str] = set()
        self._build_layout()
        self._show_view("dashboard")

    # ── Layout ────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Left sidebar
        self.sidebar = ctk.CTkFrame(
            self, fg_color=COLORS["sidebar"], width=220, corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App title / logo area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 6), padx=16)
        ctk.CTkLabel(
            logo_frame,
            text="💰 Budget",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame,
            text="Tracker",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1).pack(
            fill="x", padx=12, pady=10
        )

        # Nav buttons
        nav_items = [
            ("dashboard",    "📊", "Dashboard"),
            ("funds",        "💼", "Income Funds"),
            ("transactions", "📋", "Transactions"),
            ("reports",      "📈", "Reports"),
            ("settings",     "⚙️",  "Settings"),
        ]
        self._nav_btns: dict[str, NavButton] = {}
        for key, icon, label in nav_items:
            btn = NavButton(self.sidebar, text=label, icon=icon,
                            command=lambda k=key: self._show_view(k))
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = btn

        # Bottom version label
        ctk.CTkLabel(
            self.sidebar,
            text="v1.0  |  Offline",
            font=("Segoe UI", 10),
            text_color=COLORS["subtext"],
        ).pack(side="bottom", pady=12)

        # Right content area
        self.content_area = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Pre-build all views (reuse instead of recreate)
        self._views: dict[str, ctk.CTkFrame] = {}
        self._dashboard_view     = DashboardView(self.content_area)
        self._funds_view         = FundsView(self.content_area,
                                              on_fund_selected=self._open_fund_transactions,
                                              on_data_changed=self._on_data_changed)
        self._transactions_view  = TransactionsView(self.content_area,
                                                    on_data_changed=self._on_data_changed)
        self._reports_view       = ReportsView(self.content_area)
        self._settings_view      = SettingsView(self.content_area,
                                                on_data_changed=self._on_data_changed)
        self._views = {
            "dashboard":    self._dashboard_view,
            "funds":        self._funds_view,
            "transactions": self._transactions_view,
            "reports":      self._reports_view,
            "settings":     self._settings_view,
        }

    def _show_view(self, key: str):
        for k, v in self._views.items():
            v.pack_forget()
        self._views[key].pack(fill="both", expand=True)
        self._current_view_key = key

        for k, btn in self._nav_btns.items():
            btn.set_active(k == key)

        # If this view was marked stale, refresh it now; otherwise leave it
        # as-is.  Dashboard/Reports are kept current via the stale-tracking in
        # _on_data_changed (and the Settings→BPI notifier), so we no longer
        # force-refresh them on every visit — that avoids needless chart/table
        # rebuilds when nothing changed.
        if key in self._stale_views:
            self._stale_views.discard(key)
            if key == "dashboard":
                self._dashboard_view.refresh()
            elif key == "reports":
                self._reports_view.refresh()
            elif key == "funds":
                self._funds_view.refresh()
            elif key == "transactions":
                self._transactions_view.refresh()

    def _open_fund_transactions(self, fund_id: int):
        self._current_fund_id = fund_id
        self._transactions_view.load_fund(fund_id)
        self._stale_views.discard("transactions")   # load_fund already refreshes it
        self._show_view("transactions")

    def _on_data_changed(self):
        """Invalidate the *other* data views after an edit.

        The view that triggered the change has already refreshed itself (with
        the lightest refresh appropriate to it), so we don't refresh the active
        view again here — we just mark every other data view stale so it
        rebuilds the next time it's visited.  Settings also calls this (after a
        BPI change) so the Dashboard picks up the new balance on next visit.
        """
        key = self._current_view_key
        for k in ("dashboard", "funds", "transactions", "reports"):
            if k != key:
                self._stale_views.add(k)


# ── Bootstrap ─────────────────────────────────────────────────────────────

def main():
    # Initialise DB (creates tables if missing)
    db.initialize_db()

    # First-run: if DB is empty, offer to import
    with db.get_connection() as conn:
        fund_count = conn.execute("SELECT COUNT(*) FROM funds").fetchone()[0]

    app = BudgetTrackerApp()

    if fund_count == 0:
        _first_run_prompt(app)

    app.mainloop()


def _first_run_prompt(app: BudgetTrackerApp):
    """Show a friendly welcome dialog on first launch (empty database)."""
    dlg = ctk.CTkToplevel(app)
    dlg.title("Welcome")
    dlg.geometry("460x230")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.configure(fg_color=COLORS["bg"])
    dlg.focus()

    ctk.CTkLabel(
        dlg,
        text="👋  Welcome to Budget Tracker!",
        font=("Segoe UI", 16, "bold"),
        text_color=COLORS["text"],
    ).pack(pady=(26, 6))
    ctk.CTkLabel(
        dlg,
        text="Let's get you started. Head to the Income Funds tab to\n"
             "add your first fund, then log transactions against it.\n\n"
             "Tip: set your bank balance in Settings.",
        font=("Segoe UI", 12),
        text_color=COLORS["subtext"],
        justify="center",
    ).pack(pady=(0, 18))

    def go_to_funds():
        dlg.destroy()
        app._show_view("funds")

    ctk.CTkButton(
        dlg, text="➕  Add my first fund", width=200,
        fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
        font=("Segoe UI", 13),
        command=go_to_funds,
    ).pack()
    ctk.CTkButton(
        dlg, text="Explore on my own", width=160,
        fg_color="transparent", hover_color=COLORS["card"],
        text_color=COLORS["subtext"], font=("Segoe UI", 12),
        command=dlg.destroy,
    ).pack(pady=(8, 0))


if __name__ == "__main__":
    main()
