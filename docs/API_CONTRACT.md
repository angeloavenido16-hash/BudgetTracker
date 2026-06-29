# API Contract

Maps each desktop `database.py` function to its REST endpoint. The backend
implements these in Phase 2 (`backend/app/routers/`).

Base URL (local): `http://localhost:8000`
Auth: `Authorization: Bearer <jwt>` on every endpoint except `/auth/login` and `/health`.

---

## Auth
| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | `/auth/login` | `{username, password}` | `{access_token, token_type}` |

## Health
| Method | Path | Returns |
|--------|------|---------|
| GET | `/health` | `{status: "ok"}` |

## Funds
| Method | Path | Desktop fn | Returns |
|--------|------|-----------|---------|
| GET | `/funds?fund_type=` | `get_funds` | `Fund[]` |
| GET | `/funds/{id}` | `get_fund` | `Fund` |
| POST | `/funds` | `add_fund` | `Fund` |
| PUT | `/funds/{id}` | `update_fund` | `Fund` |
| DELETE | `/funds/{id}` | `delete_fund` | `204` |
| GET | `/funds/summaries` | `get_all_fund_summaries` | `{[id]: Summary}` |
| GET | `/funds/{id}/summary` | `get_fund_summary` | `Summary` |

## Transactions
| Method | Path | Desktop fn | Returns |
|--------|------|-----------|---------|
| GET | `/transactions?fund_id=` | `get_transactions` | `Transaction[]` |
| POST | `/transactions` | `add_transaction` | `Transaction` |
| PUT | `/transactions/{id}` | `update_transaction` | `Transaction` |
| DELETE | `/transactions/{id}` | `delete_transaction` | `204` |

## Categories
| Method | Path | Desktop fn | Returns |
|--------|------|-----------|---------|
| GET | `/categories` | `get_categories` | `string[]` |
| POST | `/categories` | `add_category` | `201` |
| DELETE | `/categories/{name}` | `delete_category` | `204` |

## BPI balance
| Method | Path | Desktop fn | Returns |
|--------|------|-----------|---------|
| GET | `/bpi-balance` | `get_bpi_balance` | `{balance, recorded_at}` |
| PUT | `/bpi-balance` | `set_bpi_balance` | `{balance, recorded_at}` |

## Dashboard
| Method | Path | Desktop fn | Returns |
|--------|------|-----------|---------|
| GET | `/dashboard/totals` | `get_dashboard_totals` | `DashboardTotals` |
| GET | `/dashboard/spending-over-time?year=` | `get_spending_over_time` | `MonthTotal[]` |
| GET | `/dashboard/expense-by-category?fund_id=&year=` | `get_expense_by_category` | `CategoryTotal[]` |
| GET | `/dashboard/years` | `get_transaction_years` | `string[]` |

## Reports  (statistics — Year / Month / Fund filterable)
All three accept optional `year` (`"YYYY"`), `month` (`"01".."12"`) and
`fund_id`. `/reports/fund-flows` ignores `fund_id` (it *is* the per-fund view).
| Method | Path | Desktop fn | Returns |
|--------|------|-----------|---------|
| GET | `/reports/overview?year=&month=&fund_id=` | `get_report_overview` | `ReportOverview` |
| GET | `/reports/category-stats?year=&month=&fund_id=` | `get_category_statistics` | `CategoryStat[]` |
| GET | `/reports/fund-flows?year=&month=` | `get_fund_flows` | `FundFlow[]` |

---

## Schemas (Pydantic)

```jsonc
// Fund
{ "id": 1, "name": "Salary", "fund_type": "salary",
  "amount": 10000.0, "cutoff_date": "2025-01-15", "notes": "" }

// Transaction
{ "id": 1, "fund_id": 1, "category": "savings",
  "amount": 3000.0, "txn_date": "2025-01-10", "remarks": "",
  "created_at": "2025-01-10 12:00:00" }

// Summary (per fund)
{ "income": 10000.0, "expenses": 0.0, "savings": 0.0,
  "house": 0.0, "carry_over": 0.0, "remaining": 10000.0 }

// DashboardTotals  (missing_expenses = bpi_balance − non_other_remaining)
{ "total_income": 15000.0, "total_expenses": 0.0,
  "total_savings": 5000.0, "net_remaining": 20000.0,
  "non_other_remaining": 15000.0, "missing_expenses": -2000.0,
  "bpi_balance": 13000.0, "fund_count": 3 }

// MonthTotal  (spending-over-time point)
{ "month": "2025-01", "total": 150.0 }

// CategoryTotal  (expense-by-category slice)
{ "category": "Food", "total": 150.0 }

// ReportOverview
{ "total_spent": 1200.0, "txn_count": 4, "avg_txn": 300.0,
  "savings": 200.0, "avg_monthly": 600.0, "active_months": 2,
  "biggest": { "amount": 600.0, "category": "Rent",
               "txn_date": "2025-02-01", "fund_name": "Salary" },
  "busiest_month": ["2025-02", 900.0], "quietest_month": ["2025-01", 300.0],
  "mom_change": 200.0, "latest_month": ["2025-02", 900.0],
  "top_category": ["Rent", 600.0], "top_category_share": 50.0,
  "most_frequent": ["Food", 2] }

// CategoryStat
{ "category": "Rent", "total": 600.0, "count": 1,
  "avg": 600.0, "max": 600.0, "share": 50.0 }

// FundFlow
{ "id": 1, "name": "Salary", "out_flow": 1000.0,
  "in_flow": 0.0, "net": -1000.0, "count": 3 }
```
