"""
views/funds_view.py  –  List, add, edit, delete salary cutoff & special income funds.
"""
import customtkinter as ctk
from datetime import datetime
import database as db
from widgets import COLORS, SectionTitle, DataTable, ModalDialog, CalendarPicker


FUND_TYPE_OPTIONS = ["salary", "bonus", "espp", "other"]
FUND_TYPE_LABELS  = {
    "salary": "💵 Salary",
    "bonus":  "🎁 Bonus",
    "espp":   "📈 ESPP",
    "other":  "🏦 Other",
}


class FundsView(ctk.CTkFrame):
    def __init__(self, master, on_fund_selected=None, on_data_changed=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._on_fund_selected = on_fund_selected
        self._on_data_changed  = on_data_changed
        self._selected_fund_id = None
        self._masked = True
        self._pairs_cache: list = []   # cached (fund, summary) — no re-query on toggle
        self._page      = 0            # current page (0-based)
        self._page_size = 10
        # Default sort hierarchy: Remaining DESC, then CutoffDate DESC, then Name ASC
        # Stored as list of (col_idx, ascending) tuples; primary is index 0
        self._sort_col: int | None = 8   # Remaining
        self._sort_asc: bool = False     # DESC (highest first)
        self._build_ui()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        SectionTitle(hdr, "💼  Income Funds").pack(side="left")

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.pack(side="right")
        # Eye toggle — rightmost
        self._eye_btn_funds = ctk.CTkButton(
            btn_frame, text="👁", width=36,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 13),
            command=self._toggle_mask,
        )
        self._eye_btn_funds.pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_frame, text="🗑 Delete", width=90,
                      fg_color=COLORS["red"],
                      hover_color="#c0392b",
                      font=("Segoe UI", 12),
                      command=self._delete_fund).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_frame, text="✏️ Edit", width=80,
                      fg_color=COLORS["card"],
                      hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=self._edit_fund).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_frame, text="➕ Add Fund", width=110,
                      fg_color=COLORS["accent"],
                      hover_color=COLORS["accent2"],
                      font=("Segoe UI", 12),
                      command=self._add_fund).pack(side="right")

        # ── Filter bar ───────────────────────────────────────────────────
        flt = ctk.CTkFrame(self, fg_color="transparent")
        flt.pack(fill="x", padx=24, pady=(10, 4))
        ctk.CTkLabel(flt, text="Filter:", font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left", padx=(0, 6))
        self._filter_var = ctk.StringVar(value="All")
        filter_opts = ["All"] + [FUND_TYPE_LABELS[t] for t in FUND_TYPE_OPTIONS]
        ctk.CTkOptionMenu(flt, values=filter_opts,
                          variable=self._filter_var,
                          fg_color=COLORS["card"],
                          button_color=COLORS["card"],
                          button_hover_color=COLORS["card_hover"],
                          font=("Segoe UI", 12),
                          command=lambda _: (setattr(self, '_page', 0), self.refresh())).pack(side="left")

        # ── Table ────────────────────────────────────────────────────────
        self.table = DataTable(
            self,
            columns=["Name", "Type", "Cutoff Date", "Amount", "Expenses",
                     "Savings", "House", "Carry Over", "Remaining"],
            col_widths=[200, 90, 100, 100, 100, 100, 100, 100, 100],
            height=340,
            on_header_click=self._on_header_click,
        )
        self.table.pack(fill="both", expand=True, padx=24, pady=8)

        # ── Pagination bar ───────────────────────────────────────────────
        pg = ctk.CTkFrame(self, fg_color="transparent")
        pg.pack(fill="x", padx=24, pady=(0, 4))
        self._btn_prev_f = ctk.CTkButton(
            pg, text="◀ Prev", width=80,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11), command=self._prev_page)
        self._btn_prev_f.pack(side="left")
        self._lbl_page_f = ctk.CTkLabel(
            pg, text="Page 1", font=("Segoe UI", 11),
            text_color=COLORS["subtext"])
        self._lbl_page_f.pack(side="left", padx=10)
        self._btn_next_f = ctk.CTkButton(
            pg, text="Next ▶", width=80,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11), command=self._next_page)
        self._btn_next_f.pack(side="left")

        # ── Detail strip ─────────────────────────────────────────────────
        detail = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10)
        detail.pack(fill="x", padx=24, pady=(4, 16))
        self.lbl_detail = ctk.CTkLabel(
            detail,
            text="Click a fund row above, then use '→ View Transactions' to manage its expenses.",
            font=("Segoe UI", 11),
            text_color=COLORS["subtext"],
        )
        self.lbl_detail.pack(side="left", padx=14, pady=10)
        ctk.CTkButton(
            detail, text="→ View Transactions", width=160,
            fg_color=COLORS["accent2"],
            hover_color=COLORS["accent"],
            font=("Segoe UI", 12),
            command=self._open_transactions,
        ).pack(side="right", padx=14, pady=8)

        self._fund_rows: list[dict] = []
        self.refresh()

    # ── Mask helpers ─────────────────────────────────────────────────────
    def _mask(self, value: float) -> str:
        """Mask a value — Remaining is never masked (always visible)."""
        return "₱ ****" if self._masked else f"₱{value:,.2f}"

    def _toggle_mask(self):
        self._masked = not self._masked
        self._eye_btn_funds.configure(
            text="🙈" if self._masked else "👁",
            fg_color=COLORS["card"] if self._masked else COLORS["accent2"],
        )
        self._page = 0             # back to page 1 on mask toggle
        self._render_table()   # re-render from cache — no DB query

    # ── Pagination helpers ────────────────────────────────────────────────
    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_table()

    def _next_page(self):
        total_pages = max(1, -(-len(self._pairs_cache) // self._page_size))
        if self._page < total_pages - 1:
            self._page += 1
            self._render_table()

    # ── Data helpers ─────────────────────────────────────────────────────
    def _on_header_click(self, col_idx: int):
        """Toggle sort direction if same column; set ascending if new column."""
        if self._sort_col == col_idx:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_idx
            self._sort_asc = True
        self._page = 0   # reset to first page on sort change
        self.refresh()

    # Sort-key extractors indexed by column position
    # 0=Name,1=Type,2=CutoffDate,3=Amount,4=Expenses,5=Savings,6=House,7=CarryOver,8=Remaining
    def _sort_key(self, fund_and_summ: tuple) -> object:
        f, s = fund_and_summ
        col = self._sort_col
        if col == 0:  return (f["name"] or "").lower()
        if col == 1:  return (f["fund_type"] or "").lower()
        if col == 2:  return f["cutoff_date"] or ""
        if col == 3:  return f["amount"]
        if col == 4:  return s.get("expenses", 0)
        if col == 5:  return s.get("savings", 0)
        if col == 6:  return s.get("house", 0)
        if col == 7:  return s.get("carry_over", 0)
        if col == 8:  return round(s.get("remaining", 0), 2)
        return ""

    def _apply_sort_hierarchy(self):
        """Sort pairs_cache with hierarchy: primary col → Remaining DESC → Date DESC → Name ASC."""
        # Step 3: Name ASC (lowest priority)
        self._pairs_cache.sort(key=lambda p: (p[0]["name"] or "").lower())
        # Step 2: CutoffDate DESC
        self._pairs_cache.sort(key=lambda p: p[0]["cutoff_date"] or "", reverse=True)
        # Step 1: Remaining DESC
        self._pairs_cache.sort(key=lambda p: round(p[1].get("remaining", 0), 2), reverse=True)
        # Step 0: Primary column chosen by user (overrides all above)
        if self._sort_col is not None:
            self._pairs_cache.sort(key=self._sort_key, reverse=not self._sort_asc)

    def refresh(self):
        """Fetch fresh data from DB in bulk, then render."""
        flt = self._filter_var.get()
        ft  = None
        for k, v in FUND_TYPE_LABELS.items():
            if v == flt:
                ft = k
        funds = db.get_funds(fund_type=ft)

        # Single bulk call — replaces N+1 per-fund queries
        all_summaries = db.get_all_fund_summaries()
        self._pairs_cache = [(f, all_summaries.get(f["id"], {})) for f in funds]

        self._apply_sort_hierarchy()
        self._fund_rows = [p[0] for p in self._pairs_cache]
        self._render_table()

    def _render_table(self):
        """Re-render the table from the cached pairs (no DB hit), current page only."""
        total      = len(self._pairs_cache)
        page_size  = self._page_size
        total_pages = max(1, -(-total // page_size))   # ceiling division
        self._page  = max(0, min(self._page, total_pages - 1))

        start = self._page * page_size
        end   = start + page_size
        page_pairs = self._pairs_cache[start:end]
        self._fund_rows = [p[0] for p in page_pairs]

        # Update pagination controls
        self._lbl_page_f.configure(
            text=f"Page {self._page + 1} of {total_pages}  ({total} funds)")
        self._btn_prev_f.configure(state="normal" if self._page > 0 else "disabled")
        self._btn_next_f.configure(state="normal" if self._page < total_pages - 1 else "disabled")

        rows   = []
        colors = []
        for f, summ in page_pairs:
            exp  = summ.get("expenses",   0)
            sav  = summ.get("savings",    0)
            hou  = summ.get("house",      0)
            co   = summ.get("carry_over", 0)
            rem  = round(summ.get("remaining", 0), 2)
            badge = FUND_TYPE_LABELS.get(f["fund_type"], f["fund_type"])
            rows.append([
                f["name"],
                badge,
                f["cutoff_date"] or "—",
                self._mask(f["amount"]),
                self._mask(exp),
                f"₱{sav:,.2f}",
                f"₱{hou:,.2f}",
                f"₱{co:,.2f}",
                f"₱{rem:,.2f}",
            ])
            if rem > 0:
                colors.append(COLORS["green"])
            elif rem < 0:
                colors.append(COLORS["red"])
            else:
                colors.append(COLORS["yellow"])

        self.table.load_rows(rows, colors, on_row_click=self._select_row)
        self.table.set_sort_indicator(self._sort_col, self._sort_asc)

    def _select_row(self, idx: int):
        if 0 <= idx < len(self._fund_rows):
            self._selected_fund_id = self._fund_rows[idx]["id"]
            f    = self._fund_rows[idx]
            # look up from full cache
            summ = next((s for ff, s in self._pairs_cache if ff["id"] == f["id"]), {})
            rem  = round(summ.get("remaining", 0), 2)
            self.lbl_detail.configure(
                text=(f"Selected: {f['name']}  |  "
                      f"Amount: {self._mask(f['amount'])}  |  "
                      f"Remaining: ₱{rem:,.2f}")
            )

    def _open_transactions(self):
        if self._selected_fund_id and self._on_fund_selected:
            self._on_fund_selected(self._selected_fund_id)

    def _add_fund(self):
        dlg = FundDialog(self, title="Add Fund")
        self.wait_window(dlg)
        if not dlg.saved:
            return
        self.refresh()
        if self._on_data_changed:
            self._on_data_changed()

    def _edit_fund(self):
        if not self._selected_fund_id:
            _show_info(self, "Select a fund row first.")
            return
        fund = db.get_fund_by_id(self._selected_fund_id)
        if not fund:
            return
        dlg = FundDialog(self, title="Edit Fund", fund=fund)
        self.wait_window(dlg)
        if not dlg.saved:
            return
        self.refresh()
        if self._on_data_changed:
            self._on_data_changed()

    def _delete_fund(self):
        if not self._selected_fund_id:
            _show_info(self, "Select a fund row first.")
            return
        fund = db.get_fund_by_id(self._selected_fund_id)
        if not fund:
            return
        ConfirmDelete(self, fund["name"], lambda: self._do_delete())

    def _do_delete(self):
        db.delete_fund(self._selected_fund_id)
        self._selected_fund_id = None
        self.lbl_detail.configure(
            text="Click a fund row above, then use '→ View Transactions' to manage its expenses."
        )
        self.refresh()
        if self._on_data_changed:
            self._on_data_changed()


# ── Fund Dialog ────────────────────────────────────────────────────────────

class FundDialog(ModalDialog):
    """
    Add / Edit a fund.
    • Salary type  → user picks Cutoff Date from calendar only;
                      Name auto-fills as "MM/DD/YYYY Salary"
    • Other types  → user enters Name + picks date from calendar
    """

    def __init__(self, master, title="Fund", fund: dict = None):
        from datetime import date as _date
        super().__init__(master, title=title, width=480, height=540)
        self._fund   = fund
        self._selected_date: str | None = (
            fund["cutoff_date"] if fund else _date.today().strftime("%Y-%m-%d")
        )
        c = self.content

        # ── Type selector ─────────────────────────────────────────────────
        type_row = ctk.CTkFrame(c, fg_color="transparent")
        type_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(type_row, text="Type", width=100, anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left")
        self._type_var = ctk.StringVar(
            value=FUND_TYPE_LABELS.get(fund["fund_type"],
                   FUND_TYPE_LABELS["salary"]) if fund else FUND_TYPE_LABELS["salary"]
        )
        ctk.CTkOptionMenu(
            type_row,
            values=list(FUND_TYPE_LABELS.values()),
            variable=self._type_var,
            fg_color=COLORS["card"],
            button_color=COLORS["card"],
            button_hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12),
            command=self._on_type_change,
        ).pack(side="left", fill="x", expand=True)

        # ── Name row (hidden for salary) ──────────────────────────────────
        self._name_row = ctk.CTkFrame(c, fg_color="transparent")
        self._name_row.pack(fill="x", pady=4)
        ctk.CTkLabel(self._name_row, text="Name", width=100, anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left")
        self.e_name = ctk.CTkEntry(
            self._name_row,
            placeholder_text="e.g. ESPP June 2026",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            font=("Segoe UI", 12),
        )
        self.e_name.pack(side="left", fill="x", expand=True)
        if fund and fund["fund_type"] != "salary":
            self.e_name.insert(0, fund["name"])

        # ── Amount row ────────────────────────────────────────────────────
        amt_row = ctk.CTkFrame(c, fg_color="transparent")
        amt_row.pack(fill="x", pady=4)
        ctk.CTkLabel(amt_row, text="Amount (₱)", width=100, anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left")
        self.e_amount = ctk.CTkEntry(
            amt_row,
            placeholder_text="0.00",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            font=("Segoe UI", 12),
        )
        self.e_amount.pack(side="left", fill="x", expand=True)
        if fund:
            self.e_amount.insert(0, str(fund["amount"]))

        # ── Selected date label ───────────────────────────────────────────
        date_hdr = ctk.CTkFrame(c, fg_color="transparent")
        date_hdr.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(date_hdr, text="Cutoff Date", width=100, anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left")
        self.lbl_date = ctk.CTkLabel(
            date_hdr,
            text=self._selected_date or "— pick from calendar —",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["accent"],
        )
        self.lbl_date.pack(side="left")

        # ── Calendar ──────────────────────────────────────────────────────
        self.calendar = CalendarPicker(
            c,
            initial_date=self._selected_date,
            on_select=self._on_date_pick,
        )
        self.calendar.pack(pady=(2, 4))

        # ── Notes (non-salary only) ───────────────────────────────────────
        self._notes_row = ctk.CTkFrame(c, fg_color="transparent")
        self._notes_row.pack(fill="x", pady=4)
        ctk.CTkLabel(self._notes_row, text="Notes", width=100, anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left")
        self.e_notes = ctk.CTkEntry(
            self._notes_row,
            placeholder_text="(optional)",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            font=("Segoe UI", 12),
        )
        self.e_notes.pack(side="left", fill="x", expand=True)
        if fund:
            self.e_notes.insert(0, fund["notes"] or "")

        self._ok_cancel(self._save)

        # Apply initial visibility based on type
        self._on_type_change(self._type_var.get())

    # ── Helpers ───────────────────────────────────────────────────────────

    def _on_date_pick(self, date_str: str):
        """Called by calendar when a day is clicked."""
        self._selected_date = date_str
        self.lbl_date.configure(text=date_str)
        # Auto-fill name for salary
        if self._get_ftype() == "salary":
            try:
                from datetime import datetime
                d = datetime.strptime(date_str, "%Y-%m-%d")
                self._auto_name = d.strftime("%m/%d/%Y") + " Salary"
            except ValueError:
                self._auto_name = date_str + " Salary"

    def _get_ftype(self) -> str:
        label = self._type_var.get()
        for k, v in FUND_TYPE_LABELS.items():
            if v == label:
                return k
        return "other"

    def _on_type_change(self, _=None):
        """Show/hide the Name row depending on selected type."""
        is_salary = (self._get_ftype() == "salary")
        if is_salary:
            self._name_row.pack_forget()
        else:
            # Re-insert name row right after type row (before amount)
            self._name_row.pack(fill="x", pady=4,
                                before=self.e_amount.master)

    def _save(self):
        ftype  = self._get_ftype()
        date_s = self._selected_date

        if not date_s:
            _show_info(self, "Please select a date from the calendar.")
            return

        # Auto-generate name for salary
        if ftype == "salary":
            from datetime import datetime
            try:
                d = datetime.strptime(date_s, "%Y-%m-%d")
                name = d.strftime("%m/%d/%Y") + " Salary"
            except ValueError:
                name = date_s + " Salary"
        else:
            name = self.e_name.get().strip()
            if not name:
                _show_info(self, "Please enter a name.")
                return

        try:
            amount = float(self.e_amount.get().strip())
        except ValueError:
            amount = 0.0

        notes = self.e_notes.get().strip() or None

        if self._fund:
            db.update_fund(self._fund["id"], name, ftype, amount,
                           date_s, notes)
        else:
            db.add_fund(name, ftype, amount, date_s, notes)
        self.saved = True
        self.destroy()


# ── Confirm delete helper ──────────────────────────────────────────────────

class ConfirmDelete(ctk.CTkToplevel):
    def __init__(self, master, item_name: str, on_confirm):
        super().__init__(master)
        self.title("Confirm Delete")
        self.geometry("360x160")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=COLORS["bg"])

        ctk.CTkLabel(
            self,
            text=f"Delete  \"{item_name}\"?\nThis cannot be undone.",
            font=("Segoe UI", 13),
            text_color=COLORS["text"],
            justify="center",
        ).pack(pady=(24, 14))

        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.pack()
        ctk.CTkButton(fr, text="Delete", width=100,
                      fg_color=COLORS["red"], hover_color="#c0392b",
                      command=lambda: [on_confirm(), self.destroy()]).pack(side="left", padx=8)
        ctk.CTkButton(fr, text="Cancel", width=90,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      command=self.destroy).pack(side="left")


def _show_info(master, msg):
    dlg = ctk.CTkToplevel(master)
    dlg.title("Info")
    dlg.geometry("320x120")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.configure(fg_color=COLORS["bg"])
    ctk.CTkLabel(dlg, text=msg, font=("Segoe UI", 12),
                 text_color=COLORS["text"], wraplength=280).pack(expand=True)
    ctk.CTkButton(dlg, text="OK", width=80,
                  fg_color=COLORS["accent"],
                  command=dlg.destroy).pack(pady=10)
