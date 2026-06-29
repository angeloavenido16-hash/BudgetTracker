# Financial Formulas — Source of Truth

> ⭐ This is the **single most important document** in the migration.
> The web app's numbers must match the desktop app exactly. These formulas are
> ported verbatim into `backend/app/services/summaries.py` and locked by
> `backend/tests/test_formula_parity.py`.

Source of truth in the desktop app: `database.py` →
`get_all_fund_summaries()` and `get_dashboard_totals()`.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Fund** | An income source (a row in `funds`). Has `amount` (= income) and `fund_type`. |
| **fund_type** | One of `salary`, `bonus`, `espp`, `other`. |
| **Transaction** | One expense/saving entry against a fund. Has signed `amount` + `category`. |
| **"other" fund** | `fund_type = 'other'`. Treated as **savings buckets**, not spending income. |
| **non-other fund** | Any fund where `fund_type != 'other'`. Real spending income. |

Category matching is **case-insensitive**. Carry over matches both
`"carry over"` and `"carry_over"`.

---

## Per-Fund Summary

For a single fund with `income = fund.amount` and its list of transactions:

| Field | Formula |
|-------|---------|
| **Expenses** | `SUM(t.amount)` over **all** transactions (signed) |
| **Savings** | `SUM(t.amount)` where `category == "savings"` **and** `t.amount > 0` |
| **Carry Over** | `SUM(t.amount)` where `category in ("carry over","carry_over")` **and** `t.amount > 0` |
| **House** | `SUM(t.amount)` where `category == "house"` (**both** signs) |
| **Remaining** | `income − Expenses` |

> Note the asymmetry:
> - **Savings** and **Carry Over** are *positive-only* (a negative entry does not reduce them).
> - **House** counts both signs.
> - **Expenses** is the raw signed sum of every transaction.

All money values are `round(x, 2)`.

---

## "Other" Fund — Savings Card Override

On the **Funds** view, the *Savings* card shown for an **"other"** fund is **not**
the per-fund Savings above. It is overridden to:

```
savings_card_value = House + Remaining        (only when fund_type == "other")
```

For every non-other fund, the Savings card shows the normal per-fund `Savings`.

(Implemented as `savings_card_value(fund_type, summary)` in `summaries.py`.)

---

## Dashboard Totals

Computed across **all** funds and transactions:

### Total Income
```
SUM(fund.amount) WHERE fund_type != 'other'
```
Only real spending income — "other" (savings buckets) excluded.

### Total Expenses
```
SUM(t.amount) for transactions on funds WHERE fund_type != 'other'
```
Raw signed sum of all transactions on non-other funds.

### Total Savings
```
SUM(other.amount) − SUM(t.amount on other funds)
```
= the **Remaining** of the "other" funds (money parked in savings buckets).

### Net Remaining
```
SUM(all funds.amount) − SUM(all transactions.amount)
```
Remaining across every fund, regardless of type.

### Non-Other Remaining (helper)
```
Total Income − SUM(t.amount on non-other funds)
```
= Total Income − Total Expenses. Used by Missing Expenses below.

### Missing Expenses
```
Missing Expenses = BPI balance − Non-Other Remaining
```
Where **BPI balance** is the latest row in `bpi_balance`. This flags the gap
between what the bank says you have and what the non-other funds say should
remain.

---

## Worked Example (locked in parity tests)

Funds:
| name | type | amount |
|------|------|--------|
| Salary | salary | 10000 |
| Bonus | bonus | 5000 |
| Other | other | 8000 |

Transactions:
| fund | category | amount |
|------|----------|--------|
| Other | savings | 3000 |

BPI balance = 13000.

Expected dashboard:
- **Total Income** = 10000 + 5000 = **15000** (Other excluded)
- **Total Expenses** = **0** (only txn is on Other)
- **Total Savings** = 8000 − 3000 = **5000** (Remaining of Other)
- **Net Remaining** = (10000+5000+8000) − 3000 = **20000**
- **Non-Other Remaining** = 15000 − 0 = **15000**
- **Missing Expenses** = 13000 − 15000 = **−2000**

---

## Dashboard Charts

Two charts on the Dashboard, both filterable by a single **Year** (`"YYYY"`,
or `null` = all years). Years come from `txn_date`, *independent of fund*.

### Spending Over Time (line chart)
```
For each txn where amount > 0 and txn_date is set (and matches year filter):
    bucket[ txn_date[:7] ] += amount         # group by "YYYY-MM"
Return sorted by month ascending → [(month, total), …]
```
**Positive amounts only** (negatives ignored). Ported as
`compute_spending_over_time(txns, year=None)`.

### Top Expense Categories (pie chart)
```
For each txn where amount > 0 (optional fund_id / year filter):
    bucket[ category ] += amount
Return sorted by total descending → [(category, total), …]
```
Ported as `compute_expense_by_category(txns, fund_id=None, year=None)`. The UI
then drops system categories (savings, carry over, payment, interest, tax,
refund) and keeps the top 7 for the pie.

### Year options
`compute_transaction_years(txns)` → distinct `txn_date[:4]`, newest first.
Drives the Year dropdown on both Dashboard and Reports.

---

## Reports — Statistics (Year / Month / Fund filterable)

The Reports view is **numbers-first** (no charts; those live on the Dashboard).
All three tabs share an optional filter triple:

- **year**  → `txn_date[:4] == "YYYY"`
- **month** → `txn_date[5:7] == "MM"`  (independent of year, so they combine)
- **fund_id** → single fund (the *Ins & Outs* tab ignores this — it *is* the
  per-fund view; year + month still apply there)

Spending is **positive amounts only** throughout. Ported as
`_txn_matches()` + the three `compute_*` functions below.

### Tab 1 — Overview (`compute_report_overview`)
| Field | Meaning |
|-------|---------|
| `total_spent` | SUM(positive amounts) in scope |
| `txn_count` | count of positive txns |
| `avg_txn` | `total_spent / txn_count` |
| `savings` | SUM(positive `savings` category) |
| `active_months` | distinct `YYYY-MM` with spending |
| `avg_monthly` | `total_spent / active_months` |
| `busiest_month` / `quietest_month` | month with max / min spend |
| `biggest` | single largest expense (+ category, date, fund_name) |
| `top_category` / `top_category_share` | biggest category and its % of total |
| `most_frequent` | category with the most transactions |
| `mom_change` | % change of latest month vs previous |
| `latest_month` | most recent `(month, total)` |

### Tab 2 — Category Stats (`compute_category_statistics`)
Per category (positive spend), sorted by `total` desc:
`total`, `count`, `avg = total/count`, `max` (biggest single), and
`share = total / grand_total × 100`.

### Tab 3 — Ins & Outs (`compute_fund_flows`)
Per fund (funds with no activity still listed, zeroed):
```
out_flow = SUM(amount)  where amount > 0      # money spent
in_flow  = SUM(-amount) where amount < 0      # refunds / reversals
net      = in_flow − out_flow                 # negative = net spending
count    = number of txns in scope
```
Sorted by `out_flow` descending.

---

## Migration rule

⚠ **Do not "improve" these formulas during migration.** Port them exactly.
If a number looks wrong, it is intentional desktop behaviour — change it only as
a *separate, deliberate* decision after parity is confirmed.
