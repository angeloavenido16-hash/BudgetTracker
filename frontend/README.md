# Frontend — React + Vite + TypeScript

Single-page app that replaces the desktop customtkinter UI.

## Stack
- **Vite + React 18 + TypeScript** — fast dev server & build
- **TanStack Table v8** — the data grids (Funds, Transactions) with sorting + pagination
- **TanStack Query (React Query)** — server state + cache invalidation (replaces the desktop "stale views" refresh model)
- **Recharts** — charts (replaces matplotlib)
- **React Router** — page navigation (replaces `_show_view`)
- **Axios** — API client

## Folder layout
```
frontend/
├── README.md
├── package.json
├── index.html
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx                 # router + sidebar layout
    ├── theme.ts                # ⭐ ported color palette
    ├── api/
    │   └── client.ts           # axios instance + auth interceptor
    ├── hooks/                  # React Query hooks (useFunds, useTransactions…)
    ├── components/
    │   ├── Sidebar.tsx
    │   ├── StatCard.tsx
    │   ├── CategoryPicker.tsx  # searchable, locked-to-list
    │   ├── CalendarPicker.tsx  # 3-level drill-down
    │   └── MaskToggle.tsx
    └── pages/
        ├── Dashboard.tsx
        ├── Funds.tsx
        ├── Transactions.tsx
        ├── Reports.tsx
        └── Settings.tsx
```

## Setup (Phase 4)
```powershell
cd frontend
npm install
npm run dev          # → http://localhost:5173
```

## Page build order (each maps to a desktop view)
| Desktop view | React page | Key pieces |
|---|---|---|
| `dashboard.py` | `Dashboard.tsx` | 6 StatCards + 2 Recharts |
| `funds_view.py` | `Funds.tsx` | TanStack Table, sort hierarchy, pagination(10), masking, CRUD modal |
| `transactions_view.py` | `Transactions.tsx` | Fund nav panel, 6 cards, table, pagination(20), CategoryPicker |
| `reports_view.py` | `Reports.tsx` | 3 chart tabs |
| `settings_view.py` | `Settings.tsx` | BPI, categories, Excel upload |

## Notes
- **Masking** is a client-side display toggle (don't send unmasked/masked to API).
- **Sort hierarchy** for Funds: Remaining DESC → Cutoff Date DESC → Name ASC.
- Pagination resets to page 1 on sort/filter/mask change (same as desktop).
