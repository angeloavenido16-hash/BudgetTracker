import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type {
  ReportOverview,
  CategoryStat,
  FundFlow,
  ReportFilters,
} from "../api/types";

/**
 * Reports hooks — mirror the desktop Reports view's three statistical tabs.
 * All accept the shared Year / Month / Fund filters (see docs/FORMULAS.md).
 *
 * Endpoints (see docs/API_CONTRACT.md):
 *   GET /reports/overview        → ReportOverview
 *   GET /reports/category-stats  → CategoryStat[]
 *   GET /reports/fund-flows      → FundFlow[]   (ignores fund_id)
 */

/** Build the axios query params from the shared filter triple. */
function toParams({ year, month, fundId }: ReportFilters) {
  const params: Record<string, string | number> = {};
  if (year && year !== "All") params.year = year;
  if (month && month !== "All") params.month = month;
  if (fundId) params.fund_id = fundId;
  return params;
}

/** GET /reports/overview — headline budget statistics + insight fields. */
export function useReportOverview(filters: ReportFilters) {
  return useQuery({
    queryKey: ["report-overview", filters],
    queryFn: async () => {
      const { data } = await api.get<ReportOverview>("/reports/overview", {
        params: toParams(filters),
      });
      return data;
    },
  });
}

/** GET /reports/category-stats — per-category spend table. */
export function useCategoryStats(filters: ReportFilters) {
  return useQuery({
    queryKey: ["report-category-stats", filters],
    queryFn: async () => {
      const { data } = await api.get<CategoryStat[]>("/reports/category-stats", {
        params: toParams(filters),
      });
      return data;
    },
  });
}

/** GET /reports/fund-flows — per-fund ins/outs. fund_id is intentionally
 *  omitted: this tab IS the per-fund view (year + month still apply). */
export function useFundFlows(filters: ReportFilters) {
  return useQuery({
    queryKey: ["report-fund-flows", { year: filters.year, month: filters.month }],
    queryFn: async () => {
      const { data } = await api.get<FundFlow[]>("/reports/fund-flows", {
        params: toParams({ year: filters.year, month: filters.month }),
      });
      return data;
    },
  });
}

/** GET /dashboard/years — distinct transaction years, newest first.
 *  Shared by the Reports + Dashboard year filters. */
export function useTransactionYears() {
  return useQuery({
    queryKey: ["transaction-years"],
    queryFn: async () => {
      const { data } = await api.get<string[]>("/dashboard/years");
      return data;
    },
  });
}
