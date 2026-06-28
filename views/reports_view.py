"""
views/reports_view.py  –  Spending reports & charts.
"""
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db
from widgets import COLORS, SectionTitle


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        SectionTitle(hdr, "📈  Reports").pack(side="left")
        ctk.CTkButton(hdr, text="⟳  Refresh", width=100,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=self.refresh).pack(side="right")

        # ── Tab strip ────────────────────────────────────────────────────
        tabs = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10)
        tabs.pack(fill="x", padx=24, pady=(12, 0))
        self._active_tab = "monthly"

        self.btn_monthly  = self._tab_btn(tabs, "📅 Monthly Spending", "monthly")
        self.btn_catbreak = self._tab_btn(tabs, "🏷 Category Breakdown", "category")
        self.btn_fund     = self._tab_btn(tabs, "💼 Fund Summary", "fund")

        self.btn_monthly.pack(side="left", padx=4, pady=6)
        self.btn_catbreak.pack(side="left", padx=4, pady=6)
        self.btn_fund.pack(side="left", padx=4, pady=6)

        # ── Chart area ───────────────────────────────────────────────────
        self.chart_area = ctk.CTkFrame(self, fg_color=COLORS["card"],
                                        corner_radius=12)
        self.chart_area.pack(fill="both", expand=True, padx=24, pady=12)

        self.refresh()

    def _tab_btn(self, parent, label, key):
        btn = ctk.CTkButton(
            parent, text=label, width=180,
            fg_color=COLORS["accent"] if key == self._active_tab else "transparent",
            hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12),
            command=lambda k=key: self._switch_tab(k),
        )
        return btn

    def _switch_tab(self, key):
        self._active_tab = key
        for btn, k in [(self.btn_monthly, "monthly"),
                       (self.btn_catbreak, "category"),
                       (self.btn_fund, "fund")]:
            btn.configure(fg_color=COLORS["accent"] if k == key else "transparent")
        self.refresh()

    def refresh(self):
        for w in self.chart_area.winfo_children():
            w.destroy()
        if self._active_tab == "monthly":
            self._draw_monthly()
        elif self._active_tab == "category":
            self._draw_category()
        else:
            self._draw_fund_summary()

    # ── Monthly bar chart ─────────────────────────────────────────────────
    def _draw_monthly(self):
        data = db.get_spending_over_time()
        if not data:
            self._no_data(); return

        months = [d[0] for d in data]
        totals = [d[1] for d in data]

        fig = Figure(figsize=(10, 4.5), dpi=92, facecolor=COLORS["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(COLORS["input_bg"])

        bars = ax.bar(range(len(months)), totals,
                      color=COLORS["accent"], alpha=0.85, edgecolor="none")
        # highlight last bar
        if bars:
            bars[-1].set_color(COLORS["yellow"])

        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right",
                           fontsize=7.5, color=COLORS["subtext"])
        ax.tick_params(axis="y", colors=COLORS["subtext"], labelsize=7.5)
        ax.set_ylabel("Total Spent (₱)", color=COLORS["subtext"], fontsize=9)
        ax.set_title("Monthly Total Spending", color=COLORS["text"], fontsize=12)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["border"])
        fig.tight_layout(pad=1.2)
        self._embed(fig)

    # ── Category horizontal bar ───────────────────────────────────────────
    def _draw_category(self):
        skip = {"savings", "carry over", "carry_over", "payment",
                 "interest", "tax", "refund", "transfer"}
        data = [(c, v) for c, v in db.get_expense_by_category()
                if c.lower() not in skip and v > 0][:20]
        if not data:
            self._no_data(); return

        labels = [d[0] for d in data][::-1]
        values = [d[1] for d in data][::-1]

        fig = Figure(figsize=(10, max(4, len(labels) * 0.32)), dpi=92,
                     facecolor=COLORS["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(COLORS["input_bg"])

        ys = range(len(labels))
        bars = ax.barh(list(ys), values,
                       color=COLORS["accent2"], alpha=0.85, edgecolor="none")
        ax.set_yticks(list(ys))
        ax.set_yticklabels(labels, fontsize=8, color=COLORS["text"])
        ax.tick_params(axis="x", colors=COLORS["subtext"], labelsize=7.5)
        ax.set_xlabel("Total (₱)", color=COLORS["subtext"], fontsize=9)
        ax.set_title("Top Expense Categories (All Time)", color=COLORS["text"], fontsize=12)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["border"])
        fig.tight_layout(pad=1.2)
        self._embed(fig)

    # ── Fund summary bar ──────────────────────────────────────────────────
    def _draw_fund_summary(self):
        funds = db.get_funds()
        if not funds:
            self._no_data(); return

        names    = [f["name"][:22] for f in funds]
        incomes  = [f["amount"] for f in funds]
        expenses = []
        for f in funds:
            summ = db.get_fund_summary(f["id"])
            expenses.append(summ.get("expenses", 0))

        x = range(len(names))
        fig = Figure(figsize=(max(8, len(names) * 0.55), 4.5),
                     dpi=92, facecolor=COLORS["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(COLORS["input_bg"])

        w = 0.35
        ax.bar([i - w/2 for i in x], incomes,  width=w,
               label="Income",   color=COLORS["green"],  alpha=0.85)
        ax.bar([i + w/2 for i in x], expenses, width=w,
               label="Expenses", color=COLORS["red"],    alpha=0.85)

        ax.set_xticks(list(x))
        ax.set_xticklabels(names, rotation=60, ha="right",
                           fontsize=6.5, color=COLORS["subtext"])
        ax.tick_params(axis="y", colors=COLORS["subtext"], labelsize=7)
        ax.set_title("Income vs Expenses per Fund", color=COLORS["text"], fontsize=12)
        ax.legend(fontsize=8, labelcolor=COLORS["subtext"],
                  frameon=False)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["border"])
        fig.tight_layout(pad=1.2)
        self._embed(fig)

    def _embed(self, fig):
        canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _no_data(self):
        ctk.CTkLabel(self.chart_area, text="No data to display yet.",
                     font=("Segoe UI", 13), text_color=COLORS["subtext"]
                     ).pack(expand=True, pady=60)
