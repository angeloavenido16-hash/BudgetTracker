/** Shared types mirroring the backend Pydantic schemas (see docs/API_CONTRACT.md). */

export type FundType = "salary" | "bonus" | "espp" | "other";

/** Auth — JWT issued by POST /auth/login. */
export interface Token {
  access_token: string;
  token_type: string;
}

/** Latest bank balance snapshot (GET/PUT /bpi-balance). */
export interface BpiBalance {
  balance: number;
  recorded_at: string | null;
}

export interface Fund {
  id: number;
  name: string;
  fund_type: FundType;
  amount: number;
  cutoff_date: string | null;
  notes: string | null;
}

export interface Transaction {
  id: number;
  fund_id: number;
  category: string;
  amount: number;
  txn_date: string | null;
  remarks: string | null;
  created_at: string;
  /** Joined from funds.name by the list/detail endpoints. */
  fund_name?: string | null;
}

export interface FundSummary {
  income: number;
  expenses: number;
  savings: number;
  house: number;
  carry_over: number;
  remaining: number;
}

export interface DashboardTotals {
  total_income: number;
  total_expenses: number;
  total_savings: number;
  net_remaining: number;
  non_other_remaining: number;
  /** bpi_balance − non_other_remaining (red when positive = unaccounted). */
  missing_expenses: number;
  bpi_balance: number;
  fund_count: number;
}

/** A single point in the "spending over time" line chart. */
export interface MonthTotal {
  month: string; // "YYYY-MM"
  total: number;
}

/** A slice in the "expense by category" pie chart. */
export interface CategoryTotal {
  category: string;
  total: number;
}

// ── Reports (statistics) ───────────────────────────────────────────────────

/** [month "YYYY-MM", total] tuple as returned by the overview endpoint. */
export type MonthPoint = [string, number];
/** [category, value] tuple (value = peso total or a count). */
export type CategoryPoint = [string, number];

export interface BiggestExpense {
  amount: number;
  category: string;
  txn_date: string | null;
  fund_name: string | null;
}

export interface ReportOverview {
  total_spent: number;
  txn_count: number;
  avg_txn: number;
  savings: number;
  avg_monthly: number;
  active_months: number;
  biggest: BiggestExpense | null;
  busiest_month: MonthPoint | null;
  quietest_month: MonthPoint | null;
  mom_change: number | null;
  latest_month: MonthPoint | null;
  top_category: CategoryPoint | null;
  top_category_share: number;
  most_frequent: CategoryPoint | null;
}

export interface CategoryStat {
  category: string;
  total: number;
  count: number;
  avg: number;
  max: number;
  share: number;
}

export interface FundFlow {
  id: number;
  name: string;
  out_flow: number;
  in_flow: number;
  net: number;
  count: number;
}

/** Shared optional filters for the Reports endpoints. */
export interface ReportFilters {
  year?: string; // "YYYY"
  month?: string; // "01".."12"
  fundId?: number;
}
