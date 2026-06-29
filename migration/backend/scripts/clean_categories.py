"""One-time cleanup: normalize category & transaction casing + fix mojibake.

Rules
-----
* Title-case each word, but keep small "filler" words lowercase unless they are
  the first/last word (the, or, of, a, an, to, for, with, …).
* Preserve known acronyms / mixed-case names (BPI, BDO, KFC, SM, ESPP, PS4 …).
* Repair mojibake produced by a bad latin-1/utf-8 round-trip ("Café" → "Café").
* Merge case-duplicates: after cleaning, `budget` + `Budget` collapse to one row,
  and every transaction is repointed to the canonical spelling.

Backs the DB up first, then runs inside a single transaction. Safe to re-run.
"""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).resolve().parents[3] / "budget_tracker.db"

FILLERS = {"the", "or", "and", "of", "a", "an", "to", "for", "with",
           "in", "on", "at", "by", "vs", "via"}
# Names whose canonical spelling is NOT plain title-case.
ACRONYMS = {
    "bpi": "BPI", "bdo": "BDO", "kfc": "KFC", "sm": "SM", "espp": "ESPP",
    "ps4": "PS4", "psp": "PSP", "hoho": "HOHO", "mnl": "MNL", "bxu": "BXU",
    "mph": "MPH", "lor": "LoR", "om": "OM", "cdc": "CDC", "gcash": "GCash",
    "tiktok": "TikTok", "le": "Le",
}


def fix_mojibake(s: str) -> str:
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def clean(name: str) -> str:
    name = fix_mojibake(name).strip()
    words = name.split()
    out: list[str] = []
    for i, w in enumerate(words):
        low = w.lower()
        if low in ACRONYMS:
            out.append(ACRONYMS[low])
        elif low in FILLERS and 0 < i < len(words) - 1:
            out.append(low)
        elif "(" in w:                       # keep "(Breakfast)" tidy
            out.append(w[0] + w[1:].title() if w[0] == "(" else w.title())
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)


def main() -> None:
    backup = DB.with_suffix(f".pre-clean-{datetime.now():%Y%m%d%H%M%S}.db")
    shutil.copy2(DB, backup)
    print(f"Backup → {backup.name}")

    con = sqlite3.connect(DB)
    cur = con.cursor()

    cats = [r[0] for r in cur.execute("SELECT name FROM expense_categories")]
    mapping = {c: clean(c) for c in cats if clean(c) != c}
    for old, new in mapping.items():
        print(f"  {old!r} → {new!r}")
        # repoint transactions, then fold the category row into the canonical one
        cur.execute("UPDATE transactions SET category=? WHERE category=?", (new, old))
        if cur.execute("SELECT 1 FROM expense_categories WHERE name=?", (new,)).fetchone():
            cur.execute("DELETE FROM expense_categories WHERE name=?", (old,))
        else:
            cur.execute("UPDATE expense_categories SET name=? WHERE name=?", (new, old))

    # also sweep any transaction categories not present in the table
    txn_cats = [r[0] for r in cur.execute("SELECT DISTINCT category FROM transactions")]
    for c in txn_cats:
        nc = clean(c)
        if nc != c:
            cur.execute("UPDATE transactions SET category=? WHERE category=?", (nc, c))

    con.commit()
    con.close()
    print(f"Done. {len(mapping)} categories cleaned.")


if __name__ == "__main__":
    main()
