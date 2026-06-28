"""
widgets.py  –  Reusable custom widgets for Budget Tracker App
"""
import calendar as _cal
from datetime import date as _date, datetime as _datetime
import customtkinter as ctk


# ── Colour palette ─────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#1a1a2e",
    "sidebar":     "#16213e",
    "card":        "#0f3460",
    "card_hover":  "#1a4a7a",
    "accent":      "#e94560",
    "accent2":     "#533483",
    "green":       "#2ecc71",
    "yellow":      "#f39c12",
    "red":         "#e74c3c",
    "text":        "#eaeaea",
    "subtext":     "#a0a0b0",
    "input_bg":    "#162447",
    "border":      "#253460",
}


class StatCard(ctk.CTkFrame):
    """A small summary card showing label + value."""

    def __init__(self, master, label: str, value: str = "₱0.00",
                 color: str = None, **kwargs):
        super().__init__(master, fg_color=COLORS["card"],
                         corner_radius=12, **kwargs)
        self._color = color or COLORS["accent"]

        accent_bar = ctk.CTkFrame(self, fg_color=self._color,
                                  height=4, corner_radius=2)
        accent_bar.pack(fill="x", padx=0, pady=(0, 0))

        self.lbl_label = ctk.CTkLabel(
            self, text=label, font=("Segoe UI", 11),
            text_color=COLORS["subtext"]
        )
        self.lbl_label.pack(padx=16, pady=(10, 2), anchor="w")

        self.lbl_value = ctk.CTkLabel(
            self, text=value, font=("Segoe UI", 22, "bold"),
            text_color=COLORS["text"]
        )
        self.lbl_value.pack(padx=16, pady=(0, 14), anchor="w")

    def set_value(self, value: str):
        self.lbl_value.configure(text=value)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master, text=text,
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["text"],
            **kwargs,
        )


class NavButton(ctk.CTkButton):
    def __init__(self, master, text: str, icon: str = "", **kwargs):
        display = f"  {icon}  {text}" if icon else text
        super().__init__(
            master,
            text=display,
            font=("Segoe UI", 13),
            fg_color="transparent",
            hover_color=COLORS["card"],
            text_color=COLORS["text"],
            anchor="w",
            height=42,
            corner_radius=8,
            **kwargs,
        )

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=COLORS["card"], text_color=COLORS["accent"])
        else:
            self.configure(fg_color="transparent", text_color=COLORS["text"])


class DataTable(ctk.CTkScrollableFrame):
    """Lightweight scrollable table built from CTkLabels.
    Supports Excel-style clickable column-header sorting.
    """

    def __init__(self, master, columns: list[str], col_widths: list[int] = None,
                 on_header_click=None, **kwargs):
        super().__init__(master, fg_color=COLORS["input_bg"],
                         corner_radius=8, **kwargs)
        self.columns         = columns
        self.col_widths      = col_widths or [150] * len(columns)
        self._on_header_click = on_header_click
        self._header_btns: list[ctk.CTkButton] = []
        self._rows: list[list[ctk.CTkLabel]] = []
        self._row_frames: list[ctk.CTkFrame] = []
        self._selected_idx: int | None = None
        self._draw_header()

    def _draw_header(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=6)
        hdr.pack(fill="x", pady=(0, 2))
        self._header_btns = []
        for i, (col, w) in enumerate(zip(self.columns, self.col_widths)):
            btn = ctk.CTkButton(
                hdr,
                text=col,
                font=("Segoe UI", 11, "bold"),
                text_color=COLORS["accent"],
                fg_color="transparent",
                hover_color=COLORS["card_hover"] if self._on_header_click else "transparent",
                anchor="w",
                width=w,
                height=30,
                cursor="hand2" if self._on_header_click else "",
                command=(lambda idx=i: self._on_header_click(idx))
                         if self._on_header_click else None,
            )
            btn.grid(row=0, column=i, padx=(4, 0), pady=3, sticky="w")
            self._header_btns.append(btn)

    def set_sort_indicator(self, col_idx: int | None, ascending: bool):
        """Show ▲ / ▼ on the active sort column; reset all others."""
        for i, btn in enumerate(self._header_btns):
            base = self.columns[i]
            if i == col_idx:
                btn.configure(
                    text=f"{base}  {'▲' if ascending else '▼'}",
                    text_color=COLORS["text"],
                )
            else:
                btn.configure(text=base, text_color=COLORS["accent"])

    def clear(self):
        for row_widgets in self._rows:
            for lbl in row_widgets:
                lbl.master.destroy()
        self._rows.clear()
        self._row_frames.clear()
        self._selected_idx = None

    def add_row(self, values: list[str], color: str = None, on_click=None):
        frame = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=4)
        frame.pack(fill="x", pady=1)
        row_idx = len(self._row_frames)
        self._row_frames.append(frame)
        row_lbls = []
        for i, (val, w) in enumerate(zip(values, self.col_widths)):
            lbl = ctk.CTkLabel(
                frame, text=str(val),
                font=("Segoe UI", 11),
                text_color=color or COLORS["text"],
                width=w, anchor="w"
            )
            lbl.grid(row=0, column=i, padx=(8, 4), pady=5, sticky="w")
            if on_click:
                lbl.bind("<Button-1>", lambda e, cb=on_click, idx=row_idx: (
                    self._set_selected(idx), cb()
                ))
            row_lbls.append(lbl)
        if on_click:
            frame.bind("<Button-1>", lambda e, cb=on_click, idx=row_idx: (
                self._set_selected(idx), cb()
            ))
        self._rows.append(row_lbls)
        return frame

    def _set_selected(self, idx: int):
        """Highlight the clicked row and un-highlight the previously selected one."""
        # Deselect old
        if self._selected_idx is not None and self._selected_idx < len(self._row_frames):
            self._row_frames[self._selected_idx].configure(fg_color=COLORS["sidebar"])
        # Select new
        self._selected_idx = idx
        if idx < len(self._row_frames):
            self._row_frames[idx].configure(fg_color=COLORS["card"])

    def load_rows(self, data: list[list], colors: list[str] = None,
                  on_row_click=None):
        self.clear()
        for i, row in enumerate(data):
            c  = colors[i] if colors and i < len(colors) else None
            cb = (lambda idx=i: on_row_click(idx)) if on_row_click else None
            self.add_row(row, color=c, on_click=cb)


class CategoryPicker(ctk.CTkFrame):
    """Search-as-you-type category picker.

    Shows a text entry; as the user types, a list of matching categories
    appears below in an auto-sizing panel that shrinks to fit the number
    of results.  Selecting an item locks the value.
    Free-typing is blocked — only list items are accepted.
    """

    MAX_VISIBLE = 6   # max rows rendered; extras prompt "keep typing"

    def __init__(self, master, categories: list[str],
                 initial: str = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._all_cats   = categories
        self._selected   = initial or ""
        self._matches: list[str] = []

        # ── Search entry row ──────────────────────────────────────────────
        entry_row = ctk.CTkFrame(self, fg_color="transparent")
        entry_row.pack(fill="x")

        self._var = ctk.StringVar(value=initial or "")
        self._entry = ctk.CTkEntry(
            entry_row,
            textvariable=self._var,
            placeholder_text="Type to search…",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            font=("Segoe UI", 12),
        )
        self._entry.pack(side="left", fill="x", expand=True)

        # Clear button
        self._btn_clear = ctk.CTkButton(
            entry_row, text="✕", width=30,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            font=("Segoe UI", 11),
            command=self._clear,
        )
        self._btn_clear.pack(side="left", padx=(4, 0))

        # ── Dropdown list (hidden until text typed) ───────────────────────
        # Plain frame auto-sizes to its children — no fixed height needed.
        self._dropdown = ctk.CTkFrame(
            self,
            fg_color=COLORS["sidebar"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=6,
        )
        # Not packed yet — shown only when there are matches

        # ── Validation state label (shown below dropdown, only when needed) ─
        self._lbl_hint = ctk.CTkLabel(
            self, text="",
            font=("Segoe UI", 10),
            text_color=COLORS["yellow"],
            anchor="w",
        )
        # Not packed at init — only shown when there is something to say

        # ── Bind events ───────────────────────────────────────────────────
        self._var.trace_add("write", self._on_type)

        # If there's an initial value, show confirmation hint immediately
        if initial:
            self._lbl_hint.configure(
                text=f"✔ {initial}", text_color=COLORS["green"]
            )
            self._lbl_hint.pack(fill="x", pady=(2, 0))

    def _show_hint(self, text: str, color: str):
        self._lbl_hint.configure(text=text, text_color=color)
        if not self._lbl_hint.winfo_ismapped():
            self._lbl_hint.pack(fill="x", pady=(2, 0))

    def _hide_hint(self):
        if self._lbl_hint.winfo_ismapped():
            self._lbl_hint.pack_forget()

    # ── Internal helpers ──────────────────────────────────────────────────
    def _on_type(self, *_):
        typed = self._var.get()

        # If user edited away from a confirmed selection, invalidate
        if typed != self._selected:
            self._selected = ""
            self._hide_hint()

        if not typed:
            self._hide_dropdown()
            return

        q = typed.lower()
        self._matches = [c for c in self._all_cats if q in c.lower()]

        if self._matches:
            self._hide_hint()          # no hint while results are visible
            self._show_dropdown(self._matches)
        else:
            self._hide_dropdown()
            self._show_hint("No match — choose from the list", COLORS["red"])

    def _show_dropdown(self, items: list[str]):
        # Clear old buttons
        for w in self._dropdown.winfo_children():
            w.destroy()

        # Only render up to MAX_VISIBLE rows; the frame auto-sizes to them
        shown = items[: self.MAX_VISIBLE]
        for cat in shown:
            ctk.CTkButton(
                self._dropdown,
                text=cat,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["card_hover"],
                text_color=COLORS["text"],
                font=("Segoe UI", 12),
                height=26,
                corner_radius=4,
                command=lambda c=cat: self._select(c),
            ).pack(fill="x", padx=2, pady=1)

        # If there are more matches than shown, hint the user to keep typing
        extra = len(items) - len(shown)
        if extra > 0:
            ctk.CTkLabel(
                self._dropdown,
                text=f"… {extra} more — keep typing to narrow down",
                anchor="w",
                font=("Segoe UI", 10, "italic"),
                text_color=COLORS["subtext"],
                height=22,
            ).pack(fill="x", padx=6, pady=(0, 2))

        if not self._dropdown.winfo_ismapped():
            self._dropdown.pack(fill="x", pady=(2, 0))

    def _hide_dropdown(self):
        if self._dropdown.winfo_ismapped():
            self._dropdown.pack_forget()

    def _select(self, cat: str):
        self._selected = cat
        self._var.set(cat)
        self._hide_dropdown()
        self._show_hint(f"✔ {cat}", COLORS["green"])
        # Move focus away from entry so no further trace fires
        self._entry.master.focus()

    def _clear(self):
        self._selected = ""
        self._var.set("")
        self._hide_dropdown()
        self._hide_hint()
        self._entry.focus()

    # ── Public API ────────────────────────────────────────────────────────
    def get(self) -> str:
        """Return the confirmed selected category, or '' if none chosen."""
        return self._selected

    def is_valid(self) -> bool:
        """True only if the user clicked a list item (not just typed text)."""
        return self._selected != "" and self._selected in self._all_cats


class CalendarPicker(ctk.CTkFrame):
    """Inline month-grid calendar with 3-level drill-down navigation.

    Day view   → click Month label → Month grid
    Month grid → click Year  label → Year  grid
    Year  grid → click a year      → back to Month grid
    Month grid → click a month     → back to Day view
    """

    DAYS_HEADER  = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    MONTH_ABBR   = [_cal.month_abbr[i] for i in range(1, 13)]
    MONTH_FULL   = [_cal.month_name[i]  for i in range(1, 13)]

    def __init__(self, master, initial_date: str = None, on_select=None, **kwargs):
        super().__init__(master, fg_color=COLORS["input_bg"],
                         corner_radius=10, **kwargs)
        self._on_select = on_select
        today = _date.today()

        if initial_date:
            try:
                d = _datetime.strptime(initial_date, "%Y-%m-%d").date()
            except ValueError:
                d = today
        else:
            d = today

        self._year       = d.year
        self._month      = d.month
        self._selected: _date | None = d
        self._view       = "day"                    # "day" | "month" | "year"
        self._year_page  = (d.year // 12) * 12     # first year of current 12-year block

        self._build()

    # ── Dispatcher ────────────────────────────────────────────────────────
    def _build(self):
        for w in self.winfo_children():
            w.destroy()
        if self._view == "day":
            self._build_day()
        elif self._view == "month":
            self._build_month()
        else:
            self._build_year()

    # ── DAY VIEW ──────────────────────────────────────────────────────────
    def _build_day(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=6, pady=(8, 4))

        ctk.CTkButton(nav, text="◀", width=28, height=26,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=self._prev_month).pack(side="left", padx=(0, 2))

        # Clickable Month label
        ctk.CTkButton(
            nav, text=self.MONTH_FULL[self._month - 1],
            width=95, height=26,
            fg_color="transparent", hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"],
            cursor="hand2",
            command=self._go_month_view,
        ).pack(side="left", padx=1)

        # Clickable Year label
        ctk.CTkButton(
            nav, text=str(self._year),
            width=52, height=26,
            fg_color="transparent", hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"],
            cursor="hand2",
            command=self._go_year_view,
        ).pack(side="left", padx=1)

        ctk.CTkButton(nav, text="▶", width=28, height=26,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=self._next_month).pack(side="right", padx=(2, 0))

        # Day-of-week header
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=8, pady=(0, 6))

        for col, day in enumerate(self.DAYS_HEADER):
            color = COLORS["subtext"] if col < 5 else COLORS["red"]
            ctk.CTkLabel(grid, text=day, width=32, height=22,
                         font=("Segoe UI", 10, "bold"),
                         text_color=color).grid(row=0, column=col, padx=1)

        # Day buttons
        for row_i, week in enumerate(_cal.monthcalendar(self._year, self._month), 1):
            for col_i, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(grid, text="", width=32, height=28
                                 ).grid(row=row_i, column=col_i, padx=1, pady=1)
                    continue
                this_date = _date(self._year, self._month, day_num)
                is_sel    = (this_date == self._selected)
                is_today  = (this_date == _date.today())

                if is_sel:
                    fg, txt = COLORS["accent"],  COLORS["text"]
                elif is_today:
                    fg, txt = COLORS["accent2"], COLORS["text"]
                else:
                    fg, txt = COLORS["card"],    COLORS["text"]

                ctk.CTkButton(
                    grid, text=str(day_num),
                    width=32, height=28,
                    font=("Segoe UI", 11),
                    fg_color=fg, hover_color=COLORS["card_hover"],
                    text_color=txt, corner_radius=6,
                    command=lambda d=this_date: self._pick_day(d),
                ).grid(row=row_i, column=col_i, padx=1, pady=1)

    # ── MONTH VIEW ────────────────────────────────────────────────────────
    def _build_month(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=6, pady=(8, 4))

        ctk.CTkButton(nav, text="◀", width=28, height=26,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=lambda: self._shift_year(-1)).pack(side="left", padx=(0, 2))

        # Clickable Year — drills into year picker
        ctk.CTkButton(
            nav, text=str(self._year),
            width=150, height=26,
            fg_color="transparent", hover_color=COLORS["card_hover"],
            font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"],
            cursor="hand2",
            command=self._go_year_view,
        ).pack(side="left", expand=True)

        ctk.CTkButton(nav, text="▶", width=28, height=26,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=lambda: self._shift_year(1)).pack(side="right", padx=(2, 0))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=10, pady=(6, 10))

        for i, abbr in enumerate(self.MONTH_ABBR):
            row, col = divmod(i, 3)
            is_cur = (i + 1 == self._month)
            ctk.CTkButton(
                grid, text=abbr,
                width=70, height=38,
                font=("Segoe UI", 12, "bold" if is_cur else "normal"),
                fg_color=COLORS["accent"] if is_cur else COLORS["card"],
                hover_color=COLORS["card_hover"],
                text_color=COLORS["text"],
                corner_radius=8,
                command=lambda m=i + 1: self._pick_month(m),
            ).grid(row=row, column=col, padx=4, pady=4)

    # ── YEAR VIEW ─────────────────────────────────────────────────────────
    def _build_year(self):
        start = self._year_page
        end   = start + 11

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=6, pady=(8, 4))

        ctk.CTkButton(nav, text="◀", width=28, height=26,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=lambda: self._shift_year_page(-12)).pack(side="left", padx=(0, 2))

        ctk.CTkLabel(nav, text=f"{start} – {end}", width=150,
                     font=("Segoe UI", 12, "bold"),
                     text_color=COLORS["text"]).pack(side="left", expand=True)

        ctk.CTkButton(nav, text="▶", width=28, height=26,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      font=("Segoe UI", 12),
                      command=lambda: self._shift_year_page(12)).pack(side="right", padx=(2, 0))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=10, pady=(6, 10))

        for i in range(12):
            yr  = start + i
            row, col = divmod(i, 3)
            is_cur = (yr == self._year)
            ctk.CTkButton(
                grid, text=str(yr),
                width=70, height=38,
                font=("Segoe UI", 12, "bold" if is_cur else "normal"),
                fg_color=COLORS["accent"] if is_cur else COLORS["card"],
                hover_color=COLORS["card_hover"],
                text_color=COLORS["text"],
                corner_radius=8,
                command=lambda y=yr: self._pick_year(y),
            ).grid(row=row, column=col, padx=4, pady=4)

    # ── Navigation helpers ────────────────────────────────────────────────
    def _go_month_view(self):
        self._view = "month"
        self._build()

    def _go_year_view(self):
        self._year_page = (self._year // 12) * 12
        self._view = "year"
        self._build()

    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._build()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._build()

    def _shift_year(self, delta: int):
        self._year += delta
        self._build()

    def _shift_year_page(self, delta: int):
        self._year_page += delta
        self._build()

    # ── Pick actions ──────────────────────────────────────────────────────
    def _pick_day(self, d: _date):
        self._selected = d
        self._year, self._month = d.year, d.month
        self._build()
        if self._on_select:
            self._on_select(d.strftime("%Y-%m-%d"))

    def _pick_month(self, month: int):
        """Select month → go back to day view."""
        self._month = month
        self._view  = "day"
        self._build()

    def _pick_year(self, year: int):
        """Select year → go back to month view."""
        self._year = year
        self._view = "month"
        self._build()

    def get_date(self) -> str | None:
        """Return selected date as 'YYYY-MM-DD', or None."""
        return self._selected.strftime("%Y-%m-%d") if self._selected else None


class ModalDialog(ctk.CTkToplevel):
    """Base modal dialog."""

    def __init__(self, master, title: str, width=480, height=420):
        super().__init__(master)
        self.saved = False          # set to True only when Save is confirmed
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self.configure(fg_color=COLORS["bg"])

        ctk.CTkLabel(
            self, text=title, font=("Segoe UI", 15, "bold"),
            text_color=COLORS["text"]
        ).pack(pady=(18, 10))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=14)

    def _ok_cancel(self, ok_cmd, ok_label="Save"):
        ctk.CTkButton(
            self.btn_frame, text=ok_label, width=110,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            command=ok_cmd
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            self.btn_frame, text="Cancel", width=90,
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            command=self.destroy
        ).pack(side="right")


def _show_info_dialog(master, msg: str):
    """Standalone info popup — importable by any view."""
    dlg = ctk.CTkToplevel(master)
    dlg.title("Info")
    dlg.geometry("320x120")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.configure(fg_color=COLORS["bg"])
    ctk.CTkLabel(
        dlg, text=msg, font=("Segoe UI", 12),
        text_color=COLORS["text"], wraplength=280
    ).pack(expand=True, padx=20)
    ctk.CTkButton(
        dlg, text="OK", width=80,
        fg_color=COLORS["accent"],
        command=dlg.destroy
    ).pack(pady=10)
