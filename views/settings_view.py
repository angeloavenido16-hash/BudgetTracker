"""
views/settings_view.py  –  App settings: categories, BPI balance, import data.
"""
import os
import customtkinter as ctk
import database as db
from widgets import COLORS, SectionTitle


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, on_import_done=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._on_import_done = on_import_done
        self._build_ui()

    def _build_ui(self):
        SectionTitle(self, "⚙️  Settings").pack(anchor="w", padx=24, pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=4)

        # ── BPI Balance ───────────────────────────────────────────────────
        self._section(scroll, "💳  BPI Current Balance")
        bpi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        bpi_row.pack(fill="x", pady=4)
        self.e_bpi = ctk.CTkEntry(
            bpi_row, placeholder_text="Enter current BPI balance",
            fg_color=COLORS["input_bg"], border_color=COLORS["border"],
            font=("Segoe UI", 13), width=220,
        )
        self.e_bpi.pack(side="left", padx=(0, 8))
        current_bpi = db.get_latest_bpi_balance()
        self.e_bpi.insert(0, f"{current_bpi:.2f}")
        ctk.CTkButton(
            bpi_row, text="Update", width=100,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            font=("Segoe UI", 12),
            command=self._save_bpi,
        ).pack(side="left")
        self.lbl_bpi_status = ctk.CTkLabel(
            bpi_row, text="", font=("Segoe UI", 11),
            text_color=COLORS["green"],
        )
        self.lbl_bpi_status.pack(side="left", padx=8)

        # ── Categories ────────────────────────────────────────────────────
        self._section(scroll, "🏷  Expense Categories")
        cat_row = ctk.CTkFrame(scroll, fg_color="transparent")
        cat_row.pack(fill="x", pady=4)
        self.e_cat = ctk.CTkEntry(
            cat_row, placeholder_text="New category name",
            fg_color=COLORS["input_bg"], border_color=COLORS["border"],
            font=("Segoe UI", 13), width=220,
        )
        self.e_cat.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            cat_row, text="Add", width=80,
            fg_color=COLORS["accent"], hover_color=COLORS["accent2"],
            font=("Segoe UI", 12),
            command=self._add_cat,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            cat_row, text="Delete Selected", width=130,
            fg_color=COLORS["red"], hover_color="#c0392b",
            font=("Segoe UI", 12),
            command=self._del_cat,
        ).pack(side="left")

        self.cat_list = ctk.CTkScrollableFrame(
            scroll, fg_color=COLORS["input_bg"],
            corner_radius=8, height=180,
        )
        self.cat_list.pack(fill="x", pady=6)
        self._cat_vars: dict[str, ctk.BooleanVar] = {}
        self._load_cats()

        # ── Import from Excel ─────────────────────────────────────────────
        self._section(scroll, "📥  Import from Excel")
        ctk.CTkLabel(
            scroll,
            text="Re-import all data from BudgetTracker_Final_Update.xlsm.\n"
                 "⚠  This will REPLACE all existing app data.",
            font=("Segoe UI", 11), text_color=COLORS["subtext"],
            justify="left",
        ).pack(anchor="w", pady=(2, 6))
        imp_row = ctk.CTkFrame(scroll, fg_color="transparent")
        imp_row.pack(fill="x", pady=4)
        ctk.CTkButton(
            imp_row, text="🔄  Import Now", width=140,
            fg_color=COLORS["accent2"], hover_color=COLORS["accent"],
            font=("Segoe UI", 13),
            command=self._run_import,
        ).pack(side="left", padx=(0, 10))
        self.lbl_import_status = ctk.CTkLabel(
            imp_row, text="", font=("Segoe UI", 11),
            text_color=COLORS["green"], wraplength=400,
        )
        self.lbl_import_status.pack(side="left")

        self.import_log = ctk.CTkTextbox(
            scroll, height=140,
            fg_color=COLORS["input_bg"],
            text_color=COLORS["subtext"],
            font=("Consolas", 10),
        )
        self.import_log.pack(fill="x", pady=6)
        self.import_log.configure(state="disabled")

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
            bal = float(self.e_bpi.get().strip())
            db.update_bpi_balance(bal)
            self.lbl_bpi_status.configure(text="✔ Saved", text_color=COLORS["green"])
        except ValueError:
            self.lbl_bpi_status.configure(text="✘ Invalid number", text_color=COLORS["red"])

    def _load_cats(self):
        for w in self.cat_list.winfo_children():
            w.destroy()
        self._cat_vars.clear()
        for cat in db.get_categories():
            var = ctk.BooleanVar()
            self._cat_vars[cat] = var
            ctk.CTkCheckBox(
                self.cat_list, text=cat, variable=var,
                font=("Segoe UI", 11),
                text_color=COLORS["text"],
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent2"],
            ).pack(anchor="w", padx=8, pady=1)

    def _add_cat(self):
        name = self.e_cat.get().strip()
        if name:
            db.add_category(name)
            self.e_cat.delete(0, "end")
            self._load_cats()

    def _del_cat(self):
        selected = [n for n, v in self._cat_vars.items() if v.get()]
        for name in selected:
            db.delete_category(name)
        self._load_cats()

    def _run_import(self):
        self.lbl_import_status.configure(text="⏳ Importing…", text_color=COLORS["yellow"])
        self.import_log.configure(state="normal")
        self.import_log.delete("1.0", "end")
        self.import_log.configure(state="disabled")
        self.update()

        try:
            import importer
            log_lines = []

            def log(msg):
                log_lines.append(msg)
                self.import_log.configure(state="normal")
                self.import_log.insert("end", msg + "\n")
                self.import_log.configure(state="disabled")
                self.import_log.see("end")
                self.update()

            importer.import_from_excel(status_callback=log)
            self.lbl_import_status.configure(
                text="✔  Import complete!", text_color=COLORS["green"]
            )
            self._load_cats()
            if self._on_import_done:
                self._on_import_done()
        except Exception as e:
            self.lbl_import_status.configure(
                text=f"✘  Error: {e}", text_color=COLORS["red"]
            )
