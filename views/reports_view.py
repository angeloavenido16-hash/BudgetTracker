"""
views/reports_view.py  –  Statistical budget report (filterable).

Unlike the Dashboard (which is chart-first and at-a-glance), Reports is
**numbers-first**: it surfaces the statistics that help you actually manage a
budget — averages, trends, concentration, biggest hits, and per-fund ins/outs.

Three tabs, each driven by the shared Year + Fund filters:
  • Overview       – headline budget statistics + insights
  • Category Stats – per-category spend / count / average / share / biggest
  • Ins & Outs     – per-fund money in (+) vs money out (−) and net flow
"""
import customtkinter as ctk

import database as db
from widgets import COLORS, SectionTitle, StatCard, DataTable


def _peso(v: float) -> str:
    return f"₱{v:,.2f}"


# Month dropdown options: label shown to the user -> "MM" value (or "" for All)
_MONTHS = [
    ("All",       "All"),
    ("January",   "01"), ("February", "02"), ("March",     "03"),
    ("April",     "04"), ("May",      "05"), ("June",      "06"),
    ("July",      "07"), ("August",   "08"), ("September", "09"),
    ("October",   "10"), ("November", "11"), ("December",  "12"),
]
_MONTH_LABEL_TO_NUM = {label: num for label, num in _MONTHS}


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._active_tab = "overview"
        self._year = "All"          # shared filter
        self._month = "All"         # shared filter (label, e.g. "January")
        self._fund = "All"          # shared filter
        self._fund_name_to_id: dict[str, int] = {}
        self._build_ui()

    # ── UI scaffold ─────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        SectionTitle(hdr, "📈  Reports").pack(side="left")
        ctk.CTkButton(hdr, text="⟳  Refresh", width=100,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=self.refresh).pack(side="right")

        # ── Filter bar (Year + Fund) ─────────────────────────────────────
        filt = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10)
        filt.pack(fill="x", padx=24, pady=(12, 0))

        ctk.CTkLabel(filt, text="Year:", font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left", padx=(14, 6), pady=10)
        self.year_filter = ctk.CTkOptionMenu(
            filt, values=["All"], width=110, font=("Segoe UI", 12),
            fg_color=COLORS["input_bg"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent2"],
            command=self._on_year_changed,
        )
        self.year_filter.set("All")
        self.year_filter.pack(side="left", pady=10)

        ctk.CTkLabel(filt, text="Month:", font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left", padx=(20, 6), pady=10)
        self.month_filter = ctk.CTkOptionMenu(
            filt, values=[label for label, _ in _MONTHS], width=130,
            font=("Segoe UI", 12),
            fg_color=COLORS["input_bg"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent2"],
            command=self._on_month_changed,
        )
        self.month_filter.set("All")
        self.month_filter.pack(side="left", pady=10)

        ctk.CTkLabel(filt, text="Fund:", font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left", padx=(20, 6), pady=10)
        self.fund_filter = ctk.CTkOptionMenu(
            filt, values=["All"], width=200, font=("Segoe UI", 12),
            fg_color=COLORS["input_bg"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent2"],
            command=self._on_fund_changed,
        )
        self.fund_filter.set("All")
        self.fund_filter.pack(side="left", pady=10)

        self.lbl_scope = ctk.CTkLabel(
            filt, text="", font=("Segoe UI", 11, "italic"),
            text_color=COLORS["subtext"])
        self.lbl_scope.pack(side="right", padx=14)

        # ── Tab strip ────────────────────────────────────────────────────
        tabs = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10)
        tabs.pack(fill="x", padx=24, pady=(10, 0))

        self.btn_overview = self._tab_btn(tabs, "📊 Overview", "overview")
        self.btn_category = self._tab_btn(tabs, "🏷 Category Stats", "category")
        self.btn_flows    = self._tab_btn(tabs, "� Ins & Outs", "flows")
        self.btn_overview.pack(side="left", padx=4, pady=6)
        self.btn_category.pack(side="left", padx=4, pady=6)
        self.btn_flows.pack(side="left", padx=4, pady=6)

        # ── Body (rebuilt per refresh) ───────────────────────────────────
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=24, pady=12)

        self.refresh()

    def _tab_btn(self, parent, label, key):
        return ctk.CTkButton(
            parent, text=label, width=170,
            fg_color=COLORS["accent"] if key == self._active_tab else "transparent",
            hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12),
            command=lambda k=key: self._switch_tab(k),
        )

    def _switch_tab(self, key):
        self._active_tab = key
        for btn, k in [(self.btn_overview, "overview"),
                       (self.btn_category, "category"),
                       (self.btn_flows, "flows")]:
            btn.configure(fg_color=COLORS["accent"] if k == key else "transparent")
        self.refresh()

    # ── Filters ──────────────────────────────────────────────────────────
    def _refresh_filter_options(self):
        years = ["All"] + db.get_transaction_years()
        self.year_filter.configure(values=years)
        if self._year not in years:
            self._year = "All"
        self.year_filter.set(self._year)

        funds = db.get_funds()
        self._fund_name_to_id = {f["name"]: f["id"] for f in funds}
        fund_opts = ["All"] + list(self._fund_name_to_id.keys())
        self.fund_filter.configure(values=fund_opts)
        if self._fund not in fund_opts:
            self._fund = "All"
        self.fund_filter.set(self._fund)

    def _on_year_changed(self, value):
        self._year = value
        self.refresh()

    def _on_month_changed(self, value):
        self._month = value
        self.refresh()

    def _on_fund_changed(self, value):
        self._fund = value
        self.refresh()

    def _year_arg(self):
        return None if self._year == "All" else self._year

    def _month_arg(self):
        """Return the "MM" value for the selected month, or None for All."""
        num = _MONTH_LABEL_TO_NUM.get(self._month, "All")
        return None if num == "All" else num

    def _fund_arg(self):
        return None if self._fund == "All" else self._fund_name_to_id.get(self._fund)

    def _scope_text(self):
        yr = "All years" if self._year == "All" else self._year
        mo = "all months" if self._month == "All" else self._month
        fn = "all funds" if self._fund == "All" else self._fund
        return f"Showing: {yr}  •  {mo}  •  {fn}"

    # ── Refresh / dispatch ───────────────────────────────────────────────
    def refresh(self):
        self._refresh_filter_options()
        self.lbl_scope.configure(text=self._scope_text())
        for w in self.body.winfo_children():
            w.destroy()
        # Guard the per-tab build so a failure shows a message instead of
        # silently leaving a blank panel (Tk swallows callback exceptions).
        try:
            if self._active_tab == "overview":
                self._build_overview()
            elif self._active_tab == "category":
                self._build_category_stats()
            else:
                self._build_flows()
        except Exception as exc:  # noqa: BLE001 — surface any build error to the UI
            import traceback
            traceback.print_exc()
            self._empty(f"Couldn't build this report:\n{exc}")

    # ── Tab 1: Overview ──────────────────────────────────────────────────
    def _build_overview(self):
        o = db.get_report_overview(year=self._year_arg(),
                                   fund_id=self._fund_arg(),
                                   month=self._month_arg())

        if not o["txn_count"]:
            self._empty("No transactions match these filters.")
            return

        # Row of stat cards
        cards = ctk.CTkFrame(self.body, fg_color="transparent")
        cards.pack(fill="x")

        stats = [
            ("Total Spent",       _peso(o["total_spent"]), COLORS["red"]),
            ("Avg / Month",       _peso(o["avg_monthly"]), COLORS["accent"]),
            ("Avg / Transaction", _peso(o["avg_txn"]),     COLORS["accent2"]),
            ("Transactions",      f"{o['txn_count']:,}",   COLORS["yellow"]),
            ("Savings Booked",    _peso(o["savings"]),     COLORS["green"]),
        ]
        for i, (label, val, color) in enumerate(stats):
            card = StatCard(cards, label, val, color=color)
            card.grid(row=0, column=i, padx=6, sticky="ew")
            cards.grid_columnconfigure(i, weight=1)

        # Insights panel
        panel = ctk.CTkFrame(self.body, fg_color=COLORS["card"], corner_radius=12)
        panel.pack(fill="both", expand=True, pady=(16, 0))
        ctk.CTkLabel(panel, text="💡  Insights",
                     font=("Segoe UI", 14, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(16, 4))

        for line in self._overview_insights(o):
            ctk.CTkLabel(panel, text=line, font=("Segoe UI", 12),
                         text_color=COLORS["subtext"], justify="left",
                         anchor="w").pack(anchor="w", padx=28, pady=3)

    def _overview_insights(self, o) -> list[str]:
        lines = []
        if o["biggest"]:
            b = o["biggest"]
            date = (b.get("txn_date") or "")[:10]
            lines.append(
                f"🔺  Biggest expense: {_peso(b['amount'])} on “{b['category']}”"
                f" ({b['fund_name']}{', ' + date if date else ''})."
            )
        if o["top_category"]:
            cat, amt = o["top_category"]
            lines.append(
                f"🏷  Top category: “{cat}” at {_peso(amt)} "
                f"— {o['top_category_share']:.0f}% of all spending."
            )
        if o["most_frequent"]:
            cat, cnt = o["most_frequent"]
            lines.append(f"🔁  Most frequent: “{cat}” with {cnt} transactions.")
        if o["busiest_month"]:
            m, v = o["busiest_month"]
            lines.append(f"📈  Busiest month: {self._fmt_month(m)} ({_peso(v)} spent).")
        if o["quietest_month"] and o["active_months"] > 1:
            m, v = o["quietest_month"]
            lines.append(f"📉  Quietest month: {self._fmt_month(m)} ({_peso(v)} spent).")
        if o["mom_change"] is not None and o["latest_month"]:
            arrow = "⬆️" if o["mom_change"] > 0 else "⬇️"
            word  = "up" if o["mom_change"] > 0 else "down"
            lm, _ = o["latest_month"]
            lines.append(
                f"{arrow}  {self._fmt_month(lm)} spending is {word} "
                f"{abs(o['mom_change']):.0f}% vs the previous month."
            )
        lines.append(
            f"📅  Activity spread across {o['active_months']} "
            f"month{'s' if o['active_months'] != 1 else ''}."
        )
        return lines

    # ── Tab 2: Category Stats ────────────────────────────────────────────
    def _build_category_stats(self):
        rows = db.get_category_statistics(year=self._year_arg(),
                                          fund_id=self._fund_arg(),
                                          month=self._month_arg())
        if not rows:
            self._empty("No spending categories match these filters.")
            return

        cols = ["Category", "Total Spent", "Txns", "Average", "% Share", "Biggest"]
        widths = [200, 140, 70, 130, 90, 130]
        table = DataTable(self.body, columns=cols, col_widths=widths)
        table.pack(fill="both", expand=True)

        data, colors = [], []
        for r in rows:
            data.append([
                r["category"],
                _peso(r["total"]),
                f"{r['count']:,}",
                _peso(r["avg"]),
                f"{r['share']:.1f}%",
                _peso(r["max"]),
            ])
            # Shade the heaviest categories red, lighter ones neutral
            colors.append(COLORS["red"] if r["share"] >= 15 else COLORS["text"])
        table.load_rows(data, colors=colors)

    # ── Tab 3: Ins & Outs ────────────────────────────────────────────────
    def _build_flows(self):
        # The Fund dropdown doesn't apply here (this tab IS the per-fund view);
        # the Year and Month filters do apply.
        rows = db.get_fund_flows(year=self._year_arg(), month=self._month_arg())
        rows = [r for r in rows if r["count"] > 0]
        if not rows:
            self._empty("No fund activity matches this year filter.")
            return

        # Totals strip
        tot_in  = sum(r["in_flow"] for r in rows)
        tot_out = sum(r["out_flow"] for r in rows)
        strip = ctk.CTkFrame(self.body, fg_color="transparent")
        strip.pack(fill="x", pady=(0, 10))
        for i, (label, val, color) in enumerate([
            ("Total In (+)",  _peso(tot_in),           COLORS["green"]),
            ("Total Out (−)", _peso(tot_out),          COLORS["red"]),
            ("Net Flow",      _peso(tot_in - tot_out), COLORS["accent"]),
        ]):
            c = StatCard(strip, label, val, color=color)
            c.grid(row=0, column=i, padx=6, sticky="ew")
            strip.grid_columnconfigure(i, weight=1)

        cols = ["Fund", "In (+)", "Out (−)", "Net", "Txns"]
        widths = [240, 150, 150, 150, 70]
        table = DataTable(self.body, columns=cols, col_widths=widths)
        table.pack(fill="both", expand=True)

        data, colors = [], []
        for r in rows:
            sign = "+" if r["net"] >= 0 else "−"
            data.append([
                r["name"],
                _peso(r["in_flow"]),
                _peso(r["out_flow"]),
                f"{sign}₱{abs(r['net']):,.2f}",
                f"{r['count']:,}",
            ])
            colors.append(COLORS["green"] if r["net"] >= 0 else COLORS["red"])
        table.load_rows(data, colors=colors)

    # ── Helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _fmt_month(month_str: str) -> str:
        try:
            year, mon = month_str.split("-")
            names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return f"{names[int(mon) - 1]} {year}"
        except (ValueError, IndexError):
            return month_str

    def _empty(self, msg: str):
        ctk.CTkLabel(self.body, text=msg, font=("Segoe UI", 13),
                     text_color=COLORS["subtext"]).pack(expand=True, pady=60)
