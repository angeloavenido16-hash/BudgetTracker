# Parity Checklist

Tick each item once the web app produces **identical** output to the desktop app.
Goal: a user switching from desktop to web sees the same numbers everywhere.

## How to verify
1. Run the desktop app, note the values on each screen.
2. Hit the matching web API endpoint (`/docs`) and/or web page.
3. Compare. They must match to the cent.

---

## Data layer
- [ ] All 4 tables migrated (`funds`, `transactions`, `expense_categories`, `bpi_balance`)
- [ ] Row counts match SQLite (run the port script's verify step)
- [ ] Fund `fund_type` values preserved (`salary`/`bonus`/`espp`/`other`)
- [ ] Transaction signs preserved (negative amounts intact)
- [ ] `cutoff_date`, `txn_date`, `created_at`, `recorded_at` preserved

## Per-fund summary (each fund)
- [ ] Expenses = signed SUM of all its transactions
- [ ] Savings = positive-only SUM of `savings` category
- [ ] Carry Over = positive-only SUM of `carry over`/`carry_over`
- [ ] House = SUM of `house` (both signs)
- [ ] Remaining = income − Expenses
- [ ] Case-insensitive category matching works

## "Other" fund override
- [ ] Savings card for `other` funds = House + Remaining
- [ ] Savings card for non-other funds = normal Savings

## Dashboard
- [ ] Total Income = SUM(non-other fund.amount)
- [ ] Total Expenses = SUM(txns on non-other funds)
- [ ] Total Savings = Remaining of "other" funds
- [ ] Net Remaining = SUM(all funds) − SUM(all txns)
- [ ] Non-Other Remaining = Total Income − Total Expenses
- [ ] Missing Expenses = BPI − Non-Other Remaining
- [ ] Missing Expenses card is RED when > 0, GREEN when ≤ 0
- [ ] BPI Balance card shows latest `bpi_balance`
- [ ] Fund count correct

## Dashboard charts (Year-filtered)
- [ ] Year dropdown lists distinct `txn_date` years, newest first
- [ ] Monthly Spending = positive amounts only, grouped by `txn_date[:7]`
- [ ] Months derive from `txn_date` (not fund), independent of fund
- [ ] Top Categories = positive amounts only, sorted desc, system cats dropped, top 7
- [ ] Both charts honour the Year filter

## Reports — statistics (Year / Month / Fund filters)
- [ ] Filters: Year (`YYYY`), Month (`01`..`12`), Fund — combine correctly
- [ ] Month filter is year-independent (matches `txn_date[5:7]`)
- [ ] Spending counts positive amounts only across all tabs
- [ ] **Overview**: total_spent, txn_count, avg_txn, savings, avg_monthly
- [ ] **Overview**: active_months, busiest/quietest month, biggest expense
- [ ] **Overview**: top_category + share, most_frequent, mom_change, latest_month
- [ ] **Category Stats**: total, count, avg, max, share per category (desc)
- [ ] **Category Stats**: rows with share ≥ 15% highlighted red
- [ ] **Ins & Outs**: out_flow (amount>0), in_flow (−amount<0), net, count
- [ ] **Ins & Outs**: funds with zero activity still listed; ignores Fund filter
- [ ] **Ins & Outs**: sorted by out_flow desc; totals strip (In/Out/Net)

## Behaviour parity
- [ ] Funds sorted by cutoff_date DESC, then name
- [ ] Funds pagination (10/page) — or intentional new value
- [ ] Transactions pagination (20/page) — or intentional new value
- [ ] Masking toggle hides/shows amounts (savings/house/carry over always shown)
- [ ] Category dropdown lists same categories
- [ ] Settings categories paginate (24/page) + searchable
- [ ] Reports/exports produce same figures

## Sign-off
- [ ] All parity tests pass (`pytest backend/tests/`)
- [ ] Manual spot-check on real data complete
- [ ] Desktop app retired / archived
