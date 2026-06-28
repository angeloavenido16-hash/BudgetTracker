"""
views/transactions_view.py  –  Manage expenses inside a selected fund.
"""
import customtkinter as ctk
from datetime import datetime
import database as db
from widgets import COLORS, SectionTitle, StatCard, DataTable, ModalDialog, CalendarPicker, CategoryPicker


class TransactionsView(ctk.CTkFrame):
    def __init__(self, master, fund_id: int = None, on_data_changed=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._fund_id = fund_id
        self._on_data_changed = on_data_changed
        self._selected_txn_id = None
        self._fund_type: str | None = None
        self._txn_rows: list[dict] = []
        self._displayed_rows: list[dict] = []
        self._displayed_rows_all: list[dict] = []   # full sorted+filtered list before pagination
        self._masked = True
        self._summ_cache: dict = {}
        self._page      = 0
        self._page_size = 20
        # sort state
        self._sort_col: int | None = 3
        self._sort_asc: bool = True
        self._build_ui()
        if fund_id:
            self.load_fund(fund_id)

    def _build_ui(self):
        # ── Top header (full width) ───────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))

        self.lbl_title = SectionTitle(hdr, "📋  Transactions")
        self.lbl_title.pack(side="left")

        btn_f = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_f.pack(side="right")
        # Eye toggle — rightmost, always visible
        self._eye_btn_txn = ctk.CTkButton(
            btn_f, text="👁", width=36,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 13),
            command=self._toggle_mask,
        )
        self._eye_btn_txn.pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_f, text="🗑 Delete", width=90,
                      fg_color=COLORS["red"], hover_color="#c0392b",
                      font=("Segoe UI", 12),
                      command=self._delete_txn).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_f, text="✏️ Edit", width=80,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=self._edit_txn).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_f, text="➕ Add", width=90,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
                      font=("Segoe UI", 12),
                      command=self._add_txn).pack(side="right")

        # ── Body: left nav + right content ───────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        # LEFT: fund navigator panel
        nav_panel = ctk.CTkFrame(body, fg_color=COLORS["sidebar"],
                                 corner_radius=10, width=210)
        nav_panel.pack(side="left", fill="y", padx=(0, 10))
        nav_panel.pack_propagate(False)
        self._build_fund_nav(nav_panel)

        # RIGHT: summary strip + search + table
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    def _build_fund_nav(self, parent):
        """Left panel: searchable list of all funds."""
        ctk.CTkLabel(parent, text="📂  Income Funds",
                     font=("Segoe UI", 12, "bold"),
                     text_color=COLORS["accent"]).pack(
                         padx=10, pady=(12, 6), anchor="w")

        # Search entry
        self._nav_search_var = ctk.StringVar()
        self._nav_search_var.trace_add("write", lambda *_: self._refresh_fund_nav())
        ctk.CTkEntry(parent, textvariable=self._nav_search_var,
                     placeholder_text="Search fund…",
                     fg_color=COLORS["input_bg"],
                     border_color=COLORS["border"],
                     font=("Segoe UI", 11),
                     height=28).pack(fill="x", padx=8, pady=(0, 6))

        # Scrollable list
        self._nav_list = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self._nav_list.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self._nav_btns: dict[int, ctk.CTkButton] = {}
        self._refresh_fund_nav()

    def _refresh_fund_nav(self):
        """Rebuild fund nav buttons (respects search filter)."""
        q = self._nav_search_var.get().lower() if hasattr(self, "_nav_search_var") else ""
        all_funds = db.get_funds()   # sorted cutoff_date DESC

        for w in self._nav_list.winfo_children():
            w.destroy()
        self._nav_btns.clear()

        for fund in all_funds:
            if q and q not in fund["name"].lower():
                continue
            is_active = (fund["id"] == self._fund_id)
            btn = ctk.CTkButton(
                self._nav_list,
                text=fund["name"],
                anchor="w",
                fg_color=COLORS["accent"]    if is_active else "transparent",
                hover_color=COLORS["accent2"] if is_active else COLORS["card_hover"],
                text_color=COLORS["bg"]      if is_active else COLORS["text"],
                font=("Segoe UI", 11),
                height=28,
                corner_radius=6,
                command=lambda fid=fund["id"]: self.load_fund(fid),
            )
            btn.pack(fill="x", pady=1, padx=2)
            self._nav_btns[fund["id"]] = btn

    def _highlight_nav(self, fund_id: int):
        """Switch the accent highlight to the newly selected fund."""
        for fid, btn in self._nav_btns.items():
            if fid == fund_id:
                btn.configure(fg_color=COLORS["accent"],
                              text_color=COLORS["bg"],
                              hover_color=COLORS["accent2"])
            else:
                btn.configure(fg_color="transparent",
                              text_color=COLORS["text"],
                              hover_color=COLORS["card_hover"])

    def _build_right(self, parent):
        """Right column: fund name + stat cards + search bar + transaction table."""
        # ── Fund name label ───────────────────────────────────────────
        self.lbl_fund_name = ctk.CTkLabel(
            parent, text="—",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["accent"],
            anchor="w",
        )
        self.lbl_fund_name.pack(fill="x", pady=(0, 6))

        # ── Stat cards row ────────────────────────────────────────────
        cards_row = ctk.CTkFrame(parent, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 8))

        self.card_income    = StatCard(cards_row, "Income",     color=COLORS["green"])
        self.card_expenses  = StatCard(cards_row, "Expenses",   color=COLORS["red"])
        self.card_savings   = StatCard(cards_row, "Savings",    color=COLORS["yellow"])
        self.card_house     = StatCard(cards_row, "House",      color=COLORS["accent"])
        self.card_carryover = StatCard(cards_row, "Carry Over", color=COLORS["subtext"])
        self.card_remaining = StatCard(cards_row, "Remaining",  color=COLORS["accent2"])

        all_cards = [self.card_income, self.card_expenses, self.card_savings,
                     self.card_house, self.card_carryover, self.card_remaining]
        for i, card in enumerate(all_cards):
            card.grid(row=0, column=i, padx=(0 if i == 0 else 4, 0), sticky="ew")
            cards_row.grid_columnconfigure(i, weight=1)

        # ── Search bar ────────────────────────────────────────────────
        search_row = ctk.CTkFrame(parent, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(search_row, text="🔍", font=("Segoe UI", 13),
                     text_color=COLORS["subtext"]).pack(side="left", padx=(0, 4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(search_row, textvariable=self._search_var,
                     placeholder_text="Search category or remarks…",
                     fg_color=COLORS["input_bg"],
                     border_color=COLORS["border"],
                     font=("Segoe UI", 12),
                     width=300).pack(side="left")

        # ── Table ─────────────────────────────────────────────────────
        self.table = DataTable(
            parent,
            columns=["#", "Category", "Amount", "Date", "Remarks"],
            col_widths=[40, 170, 110, 110, 340],
            height=340,
            on_header_click=self._on_header_click,
        )
        self.table.pack(fill="both", expand=True)

        # ── Pagination bar ────────────────────────────────────────────
        pg = ctk.CTkFrame(parent, fg_color="transparent")
        pg.pack(fill="x", pady=(4, 0))
        self._btn_prev_t = ctk.CTkButton(
            pg, text="◀ Prev", width=80,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11), command=self._prev_page)
        self._btn_prev_t.pack(side="left")
        self._lbl_page_t = ctk.CTkLabel(
            pg, text="Page 1", font=("Segoe UI", 11),
            text_color=COLORS["subtext"])
        self._lbl_page_t.pack(side="left", padx=10)
        self._btn_next_t = ctk.CTkButton(
            pg, text="Next ▶", width=80,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11), command=self._next_page)
        self._btn_next_t.pack(side="left")

    # ── Mask helpers ─────────────────────────────────────────────────────
    def _mask(self, value: float) -> str:
        """Mask a value — Amount column and Remaining card are never masked."""
        return "₱ ****" if self._masked else f"₱{value:,.2f}"

    def _toggle_mask(self):
        self._masked = not self._masked
        self._eye_btn_txn.configure(
            text="🙈" if self._masked else "👁",
            fg_color=COLORS["card"] if self._masked else COLORS["accent2"],
        )
        self._page = 0   # back to page 1
        self._apply_filter()
        self._refresh_summary_cards()

    # ── Pagination helpers ────────────────────────────────────────────────
    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_table(self._displayed_rows_all)

    def _next_page(self):
        total_pages = max(1, -(-len(self._displayed_rows_all) // self._page_size))
        if self._page < total_pages - 1:
            self._page += 1
            self._render_table(self._displayed_rows_all)

    # ── Load / Refresh ───────────────────────────────────────────────────
    def refresh(self):
        """Rebuild the fund navigator and reload the current fund's data."""
        self._refresh_fund_nav()
        if self._fund_id:
            self._load_transactions()

    def load_fund(self, fund_id: int):
        self._fund_id = fund_id
        self._selected_txn_id = None
        self._page = 0   # reset to first page on fund change
        fund = db.get_fund_by_id(fund_id)
        if fund:
            self._fund_type = fund["fund_type"]
            self.lbl_title.configure(text=f"📋  {fund['name']}")
            self.lbl_fund_name.configure(text=fund["name"])
        self._highlight_nav(fund_id)
        self._load_transactions()

    def _load_transactions(self):
        if not self._fund_id:
            return
        self._txn_rows = db.get_transactions(self._fund_id)
        self._render_table(self._txn_rows)
        self._update_summary()

    def _apply_filter(self):
        q = self._search_var.get().lower()
        filtered = [t for t in self._txn_rows
                    if q in t["category"].lower()
                    or q in (t["remarks"] or "").lower()]
        self._page = 0   # reset to page 1 on any filter change
        self._render_table(filtered)

    def _on_header_click(self, col_idx: int):
        """Toggle sort direction on same column; set ascending on new column."""
        if col_idx == 0:
            self._sort_col = None
            self._sort_asc = True
        elif self._sort_col == col_idx:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_idx
            self._sort_asc = True
        self._page = 0   # reset to first page on sort change
        self._apply_filter()

    def _sort_rows(self, txns: list[dict]) -> list[dict]:
        """Return txns sorted by the current sort column."""
        col = self._sort_col
        if col is None:
            return txns   # original order
        def key(t):
            if col == 1: return (t["category"] or "").lower()
            if col == 2: return t["amount"]
            if col == 3: return t["txn_date"] or ""
            if col == 4: return (t["remarks"] or "").lower()
            return 0
        return sorted(txns, key=key, reverse=not self._sort_asc)

    def _render_table(self, txns: list[dict]):
        txns = self._sort_rows(txns)
        self._displayed_rows_all = txns   # full list for pagination nav

        total       = len(txns)
        page_size   = self._page_size
        total_pages = max(1, -(-total // page_size))
        self._page  = max(0, min(self._page, total_pages - 1))

        start = self._page * page_size
        end   = start + page_size
        page_txns = txns[start:end]
        self._displayed_rows = page_txns

        # Update pagination controls
        self._lbl_page_t.configure(
            text=f"Page {self._page + 1} of {total_pages}  ({total} entries)")
        self._btn_prev_t.configure(state="normal" if self._page > 0 else "disabled")
        self._btn_next_t.configure(state="normal" if self._page < total_pages - 1 else "disabled")

        rows   = []
        colors = []
        for i, t in enumerate(page_txns, start + 1):   # # column shows global row number
            amt = t["amount"]
            rows.append([
                str(i),
                t["category"],
                f"₱{amt:,.2f}",
                t["txn_date"] or "—",
                t["remarks"] or "—",
            ])
            if t["category"].lower() in ("savings", "payment"):
                colors.append(COLORS["green"])
            elif t["category"].lower() in ("carry over", "carry_over"):
                colors.append(COLORS["yellow"])
            elif amt < 0:
                colors.append(COLORS["green"])
            else:
                colors.append(COLORS["text"])
        self.table.load_rows(rows, colors, on_row_click=self._select_row)
        self.table.set_sort_indicator(self._sort_col, self._sort_asc)

    def _select_row(self, idx: int):
        """Called when a table row is clicked – store the selected transaction id."""
        if 0 <= idx < len(self._displayed_rows):
            self._selected_txn_id = self._displayed_rows[idx]["id"]

    def _update_summary(self):
        """Fetch fresh summary from DB and cache it, then update cards."""
        if not self._fund_id:
            return
        self._summ_cache = db.get_fund_summary(self._fund_id)
        self._refresh_summary_cards()

    def _refresh_summary_cards(self):
        """Re-render stat cards from cache — no DB hit."""
        summ = self._summ_cache
        if not summ:
            return
        inc = summ.get("income",     0)
        exp = summ.get("expenses",   0)
        sav = summ.get("savings",    0)
        hou = summ.get("house",      0)
        co  = summ.get("carry_over", 0)
        rem = round(summ.get("remaining", 0), 2)

        # For "other" type funds, Savings card = House + Remaining
        if self._fund_type == "other":
            sav_display = round(hou + rem, 2)
        else:
            sav_display = sav

        self.card_income.set_value(    self._mask(inc))          # masked
        self.card_expenses.set_value(  self._mask(exp))          # masked
        self.card_savings.set_value(   f"₱{sav_display:,.2f}")   # always visible
        self.card_house.set_value(     f"₱{hou:,.2f}")           # always visible
        self.card_carryover.set_value( f"₱{co:,.2f}")            # always visible
        self.card_remaining.set_value( f"₱{rem:,.2f}")           # always visible

        # Colour-code Remaining value text: green > 0, yellow = 0, red < 0
        rem_color = (COLORS["green"]  if rem > 0 else
                     COLORS["yellow"] if rem == 0 else
                     COLORS["red"])
        self.card_remaining.lbl_value.configure(text_color=rem_color)

    # ── CRUD ─────────────────────────────────────────────────────────────
    def _add_txn(self):
        if not self._fund_id:
            return
        dlg = TransactionDialog(self, fund_id=self._fund_id)
        self.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_transactions()
        if self._on_data_changed:
            self._on_data_changed()

    def _edit_txn(self):
        if not self._selected_txn_id:
            return
        txn = next((t for t in self._txn_rows
                    if t["id"] == self._selected_txn_id), None)
        if not txn:
            return
        dlg = TransactionDialog(self, fund_id=self._fund_id, txn=txn)
        self.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_transactions()
        if self._on_data_changed:
            self._on_data_changed()

    def _delete_txn(self):
        if not self._selected_txn_id:
            return
        db.delete_transaction(self._selected_txn_id)
        self._selected_txn_id = None
        self._load_transactions()
        if self._on_data_changed:
            self._on_data_changed()


# ── Transaction Dialog ─────────────────────────────────────────────────────

class TransactionDialog(ModalDialog):
    def __init__(self, master, fund_id: int, txn: dict = None):
        from datetime import date as _date
        title = "Edit Transaction" if txn else "Add Transaction"
        super().__init__(master, title=title, width=480, height=600)
        self._fund_id = fund_id
        self._txn     = txn
        self._selected_date: str | None = (
            txn["txn_date"] if txn else _date.today().strftime("%Y-%m-%d")
        )
        c = self.content

        cats = db.get_categories()
        if not cats:
            cats = ["(no categories)"]

        def lbl_row(label):
            fr = ctk.CTkFrame(c, fg_color="transparent")
            fr.pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(fr, text=label, width=100, anchor="w",
                         font=("Segoe UI", 12),
                         text_color=COLORS["subtext"]).pack(side="left")
            return fr

        # ── Category — searchable picker, locked to list ───────────────────
        ctk.CTkLabel(c, text="Category", anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(fill="x", pady=(0, 2))
        default_cat = txn["category"] if txn else ""
        if default_cat and default_cat not in cats:
            cats = [default_cat] + cats
        self.cat_picker = CategoryPicker(c, categories=cats, initial=default_cat)
        self.cat_picker.pack(fill="x", pady=(0, 8))

        # ── Amount ────────────────────────────────────────────────────────
        fr_amt = lbl_row("Amount (₱)")
        self.e_amount = ctk.CTkEntry(
            fr_amt,
            placeholder_text="0.00  (use - for negative)",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            font=("Segoe UI", 12),
        )
        self.e_amount.pack(side="left", fill="x", expand=True)
        if txn:
            self.e_amount.insert(0, str(txn["amount"]))

        # ── Remarks ───────────────────────────────────────────────────────
        fr_rem = lbl_row("Remarks")
        self.e_remarks = ctk.CTkEntry(
            fr_rem,
            placeholder_text="(optional)",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            font=("Segoe UI", 12),
        )
        self.e_remarks.pack(side="left", fill="x", expand=True)
        if txn:
            self.e_remarks.insert(0, txn["remarks"] or "")

        # ── Date — calendar picker ────────────────────────────────────────
        date_hdr = ctk.CTkFrame(c, fg_color="transparent")
        date_hdr.pack(fill="x", pady=(6, 2))
        ctk.CTkLabel(date_hdr, text="Date", width=100, anchor="w",
                     font=("Segoe UI", 12),
                     text_color=COLORS["subtext"]).pack(side="left")
        self.lbl_date = ctk.CTkLabel(
            date_hdr,
            text=self._selected_date or "— pick from calendar —",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["accent"],
        )
        self.lbl_date.pack(side="left")

        self.calendar = CalendarPicker(
            c,
            initial_date=self._selected_date,
            on_select=self._on_date_pick,
        )
        self.calendar.pack(pady=(2, 4))

        self._ok_cancel(self._save)

    def _on_date_pick(self, date_str: str):
        self._selected_date = date_str
        self.lbl_date.configure(text=date_str)

    def _save(self):
        from widgets import _show_info_dialog
        cat    = self.cat_picker.get()
        amt_s  = self.e_amount.get().strip()
        rem    = self.e_remarks.get().strip()
        date_s = self._selected_date

        if not self.cat_picker.is_valid():
            _show_info_dialog(self, "Please select a category from the list.")
            return
        if not date_s:
            _show_info_dialog(self, "Please pick a date from the calendar.")
            return
            return
        try:
            amount = float(amt_s)
        except ValueError:
            return

        if self._txn:
            db.update_transaction(self._txn["id"], cat, amount,
                                  date_s, rem or None)
        else:
            db.add_transaction(self._fund_id, cat, amount,
                               date_s, rem or None)
        self.saved = True
        self.destroy()
