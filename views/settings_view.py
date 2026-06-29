"""
views/settings_view.py  –  App settings: BPI balance & expense categories.
"""
import customtkinter as ctk
import database as db
from widgets import COLORS, SectionTitle


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, on_data_changed=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._on_data_changed = on_data_changed
        self._build_ui()

    def _build_ui(self):
        SectionTitle(self, "⚙️  Settings").pack(anchor="w", padx=24, pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=4)

        # ── BPI Balance (prominent card) ─────────────────────────────────
        bpi_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=14)
        bpi_card.pack(fill="x", pady=(4, 18))

        # Accent strip on top so it's impossible to miss
        ctk.CTkFrame(bpi_card, fg_color=COLORS["accent"], height=5,
                     corner_radius=2).pack(fill="x")

        inner = ctk.CTkFrame(bpi_card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=18)

        ctk.CTkLabel(
            inner, text="💳  BPI Current Balance",
            font=("Segoe UI", 16, "bold"), text_color=COLORS["text"],
        ).pack(anchor="w")

        current_bpi = db.get_latest_bpi_balance()
        self.lbl_bpi_current = ctk.CTkLabel(
            inner, text=f"₱{current_bpi:,.2f}",
            font=("Segoe UI", 30, "bold"), text_color=COLORS["accent"],
        )
        self.lbl_bpi_current.pack(anchor="w", pady=(2, 12))

        ctk.CTkLabel(
            inner, text="Update your latest bank balance:",
            font=("Segoe UI", 11), text_color=COLORS["subtext"],
        ).pack(anchor="w", pady=(0, 4))

        edit_row = ctk.CTkFrame(inner, fg_color="transparent")
        edit_row.pack(fill="x")
        self.e_bpi = ctk.CTkEntry(
            edit_row, placeholder_text="0.00",
            fg_color=COLORS["input_bg"], border_color=COLORS["accent"],
            border_width=2, font=("Segoe UI", 16), width=240, height=44,
        )
        self.e_bpi.pack(side="left", padx=(0, 10))
        self.e_bpi.insert(0, f"{current_bpi:.2f}")
        self.e_bpi.bind("<Return>", lambda _e: self._save_bpi())

        ctk.CTkButton(
            edit_row, text="💾  Update Balance", width=170, height=44,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            font=("Segoe UI", 14, "bold"),
            command=self._save_bpi,
        ).pack(side="left")

        self.lbl_bpi_status = ctk.CTkLabel(
            edit_row, text="", font=("Segoe UI", 12, "bold"),
            text_color=COLORS["green"],
        )
        self.lbl_bpi_status.pack(side="left", padx=12)

        # ── Categories ────────────────────────────────────────────────────
        self._section(scroll, "🏷  Expense Categories")
        ctk.CTkLabel(
            scroll,
            text="Search to find a category fast, then tap its ✕ to remove it.",
            font=("Segoe UI", 11), text_color=COLORS["subtext"],
        ).pack(anchor="w", pady=(0, 6))

        # Add row (new category)
        add_row = ctk.CTkFrame(scroll, fg_color="transparent")
        add_row.pack(fill="x", pady=4)
        self.e_cat = ctk.CTkEntry(
            add_row, placeholder_text="New category name",
            fg_color=COLORS["input_bg"], border_color=COLORS["border"],
            font=("Segoe UI", 13), width=240, height=38,
        )
        self.e_cat.pack(side="left", padx=(0, 8))
        self.e_cat.bind("<Return>", lambda _e: self._add_cat())
        ctk.CTkButton(
            add_row, text="➕  Add", width=90, height=38,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            font=("Segoe UI", 13),
            command=self._add_cat,
        ).pack(side="left")
        self.lbl_cat_count = ctk.CTkLabel(
            add_row, text="", font=("Segoe UI", 11),
            text_color=COLORS["subtext"],
        )
        self.lbl_cat_count.pack(side="left", padx=12)

        # Search row — filters the chips below as you type
        search_row = ctk.CTkFrame(scroll, fg_color="transparent")
        search_row.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(search_row, text="🔍", font=("Segoe UI", 13),
                     text_color=COLORS["subtext"]).pack(side="left", padx=(0, 4))
        self._cat_search_var = ctk.StringVar()
        self._cat_search_var.trace_add("write", lambda *_: self._on_cat_search())
        ctk.CTkEntry(
            search_row, textvariable=self._cat_search_var,
            placeholder_text="Search categories…",
            fg_color=COLORS["input_bg"], border_color=COLORS["border"],
            font=("Segoe UI", 12), width=300, height=34,
        ).pack(side="left")

        # Paging state — only one page of chips is rendered at a time (fast).
        self._cat_page = 0
        self._cat_page_size = 24
        self._chip_wrap = None
        self._chip_cols = 0
        self._cat_page_items: list[str] = []

        # Chip-style flow container for the current page of categories
        self.cat_list = ctk.CTkScrollableFrame(
            scroll, fg_color=COLORS["input_bg"],
            corner_radius=10, height=240,
        )
        self.cat_list.pack(fill="x", pady=8)

        # Pagination bar
        pg = ctk.CTkFrame(scroll, fg_color="transparent")
        pg.pack(fill="x", pady=(0, 8))
        self._btn_cat_prev = ctk.CTkButton(
            pg, text="◀ Prev", width=80,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11), command=self._cat_prev_page)
        self._btn_cat_prev.pack(side="left")
        self._lbl_cat_page = ctk.CTkLabel(
            pg, text="Page 1", font=("Segoe UI", 11),
            text_color=COLORS["subtext"])
        self._lbl_cat_page.pack(side="left", padx=10)
        self._btn_cat_next = ctk.CTkButton(
            pg, text="Next ▶", width=80,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11), command=self._cat_next_page)
        self._btn_cat_next.pack(side="left")

        self._load_cats()

    # ── Helpers ──────────────────────────────────────────────────────────
    def _section(self, parent, title):
        fr = ctk.CTkFrame(parent, fg_color=COLORS["border"], height=1)
        fr.pack(fill="x", pady=(14, 4))
        ctk.CTkLabel(
            parent, text=title,
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w", pady=(2, 4))

    def _save_bpi(self):
        try:
            bal = float(self.e_bpi.get().strip().replace(",", ""))
            db.update_bpi_balance(bal)
            self.lbl_bpi_current.configure(text=f"₱{bal:,.2f}")
            self.lbl_bpi_status.configure(text="✔ Saved", text_color=COLORS["green"])
            self.after(2500, lambda: self.lbl_bpi_status.configure(text=""))
            # Dashboard's BPI + Missing-Expenses cards depend on this value.
            if self._on_data_changed:
                self._on_data_changed()
        except ValueError:
            self.lbl_bpi_status.configure(text="✘ Invalid number", text_color=COLORS["red"])

    def _load_cats(self):
        """Reload categories from the DB and re-render the current page."""
        self._cats = db.get_categories()
        self.lbl_cat_count.configure(
            text=f"{len(self._cats)} categor{'y' if len(self._cats) == 1 else 'ies'}"
        )
        self._cat_page = 0
        self._render_cat_page()

    def _filtered_cats(self) -> list[str]:
        """Categories matching the current search box (case-insensitive)."""
        q = self._cat_search_var.get().strip().lower() if hasattr(self, "_cat_search_var") else ""
        if not q:
            return self._cats
        return [c for c in self._cats if q in c.lower()]

    def _on_cat_search(self):
        """Search changed — jump back to page 1 and re-render."""
        self._cat_page = 0
        self._render_cat_page()

    def _cat_prev_page(self):
        if self._cat_page > 0:
            self._cat_page -= 1
            self._render_cat_page()

    def _cat_next_page(self):
        items = self._filtered_cats()
        total_pages = max(1, -(-len(items) // self._cat_page_size))
        if self._cat_page < total_pages - 1:
            self._cat_page += 1
            self._render_cat_page()

    def _render_cat_page(self):
        """Render only the current page of (filtered) chips — fast even with
        hundreds of categories, since at most page_size chips are built."""
        for w in self.cat_list.winfo_children():
            w.destroy()
        self._chip_wrap = None
        self._chip_cols = 0

        items       = self._filtered_cats()
        total       = len(items)
        page_size   = self._cat_page_size
        total_pages = max(1, -(-total // page_size))
        self._cat_page = max(0, min(self._cat_page, total_pages - 1))

        start = self._cat_page * page_size
        end   = start + page_size
        self._cat_page_items = items[start:end]

        # Update pagination controls
        self._lbl_cat_page.configure(
            text=f"Page {self._cat_page + 1} of {total_pages}  ({total} shown)")
        self._btn_cat_prev.configure(
            state="normal" if self._cat_page > 0 else "disabled")
        self._btn_cat_next.configure(
            state="normal" if self._cat_page < total_pages - 1 else "disabled")

        if not items:
            q = self._cat_search_var.get().strip()
            msg = (f"No categories match “{q}”." if q
                   else "No categories yet — add one above.")
            ctk.CTkLabel(
                self.cat_list, text=msg,
                font=("Segoe UI", 12), text_color=COLORS["subtext"],
            ).pack(anchor="w", padx=12, pady=12)
            return

        # Chips for THIS PAGE flow into a responsive grid that re-wraps on resize.
        self._chip_wrap = ctk.CTkFrame(self.cat_list, fg_color="transparent")
        self._chip_wrap.pack(fill="both", expand=True, padx=6, pady=6)
        self._chip_wrap.bind("<Configure>", self._on_chip_area_resize)
        # Defer first layout until the frame has a real width.
        self.after(40, lambda: self._reflow_chips(self._chip_wrap.winfo_width()))

    def _on_chip_area_resize(self, event):
        self._reflow_chips(event.width)

    def _reflow_chips(self, width: int):
        """Lay the current page's chips out in as many columns as fit."""
        if not getattr(self, "_chip_wrap", None) or not self._chip_wrap.winfo_exists():
            return
        cell = 190  # estimated chip cell width (incl. padding)
        cols = max(1, int(width) // cell)
        if cols == self._chip_cols:
            return  # column count unchanged → no need to rebuild
        self._chip_cols = cols

        for w in self._chip_wrap.winfo_children():
            w.destroy()
        for c in range(cols):
            self._chip_wrap.grid_columnconfigure(c, weight=1, uniform="chip")
        for i, name in enumerate(self._cat_page_items):
            chip = self._build_chip(self._chip_wrap, name)
            chip.grid(row=i // cols, column=i % cols,
                      padx=4, pady=4, sticky="w")

    def _build_chip(self, parent, name: str):
        """Build a pill (name + inline ✕ delete) and return its frame."""
        chip = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=14)

        ctk.CTkLabel(
            chip, text=name, font=("Segoe UI", 12),
            text_color=COLORS["text"], anchor="w",
        ).pack(side="left", padx=(12, 4), pady=4)

        ctk.CTkButton(
            chip, text="✕", width=22, height=22, corner_radius=11,
            fg_color="transparent", hover_color=COLORS["red"],
            text_color=COLORS["subtext"], font=("Segoe UI", 12, "bold"),
            command=lambda n=name: self._delete_cat(n),
        ).pack(side="left", padx=(0, 6), pady=4)
        return chip

    def _add_cat(self):
        name = self.e_cat.get().strip()
        if name:
            db.add_category(name)
            self.e_cat.delete(0, "end")
            self._load_cats()

    def _delete_cat(self, name: str):
        db.delete_category(name)
        # Keep the user on (a valid) current page instead of snapping to page 1.
        self._cats = db.get_categories()
        self.lbl_cat_count.configure(
            text=f"{len(self._cats)} categor{'y' if len(self._cats) == 1 else 'ies'}"
        )
        self._render_cat_page()
