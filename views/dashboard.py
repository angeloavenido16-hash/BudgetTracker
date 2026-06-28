"""
views/dashboard.py  –  Overview dashboard with stat cards and charts
"""
import tkinter as tk
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db
from widgets import COLORS, StatCard, SectionTitle


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._build_ui()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        SectionTitle(hdr, "📊  Dashboard").pack(side="left")
        ctk.CTkButton(
            hdr, text="⟳  Refresh", width=100,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12),
            command=self.refresh,
        ).pack(side="right")

        # ── Stat cards ───────────────────────────────────────────────────
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=24, pady=14)

        self.card_income   = StatCard(self.cards_frame, "Total Income",      color=COLORS["green"])
        self.card_expenses = StatCard(self.cards_frame, "Total Expenses",    color=COLORS["red"])
        self.card_savings  = StatCard(self.cards_frame, "Total Savings",     color=COLORS["yellow"])
        self.card_net      = StatCard(self.cards_frame, "Net Remaining",     color=COLORS["accent2"])
        self.card_bpi      = StatCard(self.cards_frame, "BPI Balance",       color=COLORS["accent"])
        self.card_missing  = StatCard(self.cards_frame, "Missing Expenses",  color=COLORS["subtext"])

        all_cards = [self.card_income, self.card_expenses, self.card_savings,
                     self.card_net, self.card_bpi, self.card_missing]
        for i, card in enumerate(all_cards):
            card.grid(row=0, column=i, padx=6, sticky="ew")
            self.cards_frame.grid_columnconfigure(i, weight=1)

        # ── Charts row ───────────────────────────────────────────────────
        charts_row = ctk.CTkFrame(self, fg_color="transparent")
        charts_row.pack(fill="both", expand=True, padx=24, pady=8)
        charts_row.grid_columnconfigure(0, weight=2)
        charts_row.grid_columnconfigure(1, weight=1)

        self.chart_left  = ctk.CTkFrame(charts_row, fg_color=COLORS["card"], corner_radius=12)
        self.chart_right = ctk.CTkFrame(charts_row, fg_color=COLORS["card"], corner_radius=12)
        self.chart_left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.chart_right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(self.chart_left,  text="Monthly Spending",
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLORS["subtext"]).pack(pady=(12, 0))
        ctk.CTkLabel(self.chart_right, text="Top Expense Categories",
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLORS["subtext"]).pack(pady=(12, 0))

        self.canvas_left_holder  = ctk.CTkFrame(self.chart_left,  fg_color="transparent")
        self.canvas_right_holder = ctk.CTkFrame(self.chart_right, fg_color="transparent")
        self.canvas_left_holder.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas_right_holder.pack(fill="both", expand=True, padx=8, pady=8)

        self.refresh()

    def refresh(self):
        totals = db.get_dashboard_totals()
        bpi    = db.get_latest_bpi_balance()

        # Missing Expenses = BPI Balance - SUM(Remaining of non-other funds)
        missing = bpi - totals["non_other_remaining"]

        self.card_income.set_value(  f"₱{totals['total_income']:,.2f}")
        self.card_expenses.set_value(f"₱{totals['total_expenses']:,.2f}")
        self.card_savings.set_value( f"₱{totals['total_savings']:,.2f}")
        self.card_net.set_value(     f"₱{totals['net_remaining']:,.2f}")
        self.card_bpi.set_value(     f"₱{bpi:,.2f}")
        self.card_missing.set_value( f"₱{missing:,.2f}")

        # Colour-code Missing Expenses: red if positive (unaccounted), green if ≤ 0
        missing_color = COLORS["red"] if missing > 0 else COLORS["green"]
        self.card_missing.lbl_value.configure(text_color=missing_color)

        self._draw_line_chart()
        self._draw_pie_chart()

    # ── Charts ────────────────────────────────────────────────────────────
    def _clear_holder(self, holder):
        for w in holder.winfo_children():
            w.destroy()

    def _draw_line_chart(self):
        self._clear_holder(self.canvas_left_holder)
        data = db.get_spending_over_time()
        if not data:
            ctk.CTkLabel(self.canvas_left_holder, text="No data yet",
                         text_color=COLORS["subtext"]).pack(expand=True)
            return

        months = [d[0] for d in data]
        totals = [d[1] for d in data]

        fig = Figure(figsize=(6, 3), dpi=90,
                     facecolor=COLORS["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(COLORS["input_bg"])
        ax.plot(months, totals, color=COLORS["accent"], linewidth=2,
                marker="o", markersize=5)
        ax.fill_between(range(len(months)), totals,
                        alpha=0.15, color=COLORS["accent"])
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right",
                           fontsize=7, color=COLORS["subtext"])
        ax.tick_params(axis="y", colors=COLORS["subtext"], labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["border"])
        ax.yaxis.label.set_color(COLORS["subtext"])
        fig.tight_layout(pad=1.0)

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_left_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_pie_chart(self):
        self._clear_holder(self.canvas_right_holder)
        data = db.get_expense_by_category()
        # top 7 categories, skip system ones
        skip = {"savings", "carry over", "carry_over", "payment",
                 "interest", "tax", "refund"}
        data = [(c, v) for c, v in data
                if c.lower() not in skip and v > 0][:7]
        if not data:
            ctk.CTkLabel(self.canvas_right_holder, text="No data yet",
                         text_color=COLORS["subtext"]).pack(expand=True)
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]
        pie_colors = ["#e94560","#533483","#2ecc71","#f39c12",
                      "#3498db","#9b59b6","#e67e22"]

        fig = Figure(figsize=(3.2, 3.2), dpi=90,
                     facecolor=COLORS["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(COLORS["card"])
        wedges, texts, autotexts = ax.pie(
            values, labels=None,
            autopct="%1.0f%%", startangle=90,
            colors=pie_colors[:len(data)],
            pctdistance=0.75,
            wedgeprops={"linewidth": 1.5, "edgecolor": COLORS["card"]},
        )
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(COLORS["text"])
        ax.legend(
            wedges, labels,
            loc="lower center",
            ncol=2,
            fontsize=6.5,
            frameon=False,
            labelcolor=COLORS["subtext"],
            bbox_to_anchor=(0.5, -0.12),
        )
        fig.tight_layout(pad=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_right_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
