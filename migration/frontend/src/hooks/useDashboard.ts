import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { DashboardTotals, MonthTotal, CategoryTotal } from "../api/types";

/** GET /dashboard/totals — the headline figures, optionally year-scoped. */
export function useDashboard(year?: string) {
  return useQuery({
    queryKey: ["dashboard", year ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<DashboardTotals>("/dashboard/totals", {
        params: year && year !== "All" ? { year } : undefined,
      });
      return data;
    },
  });
}

/** GET /dashboard/spending-over-time — monthly totals, optional year filter. */
export function useSpendingOverTime(year?: string) {
  return useQuery({
    queryKey: ["spending-over-time", year ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<MonthTotal[]>("/dashboard/spending-over-time", {
        params: year && year !== "All" ? { year } : undefined,
      });
      return data;
    },
  });
}

/** GET /dashboard/expense-by-category — pie slices, optional year filter. */
export function useExpenseByCategory(year?: string) {
  return useQuery({
    queryKey: ["expense-by-category", year ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<CategoryTotal[]>("/dashboard/expense-by-category", {
        params: year && year !== "All" ? { year } : undefined,
      });
      return data;
    },
  });
}

/** GET /dashboard/category-over-time — monthly histogram for one category.
 *  `sign`: "out" = positive/outflow, "in" = negative/inflow, undefined = all. */
export function useCategoryOverTime(category: string, year?: string, sign?: "in" | "out") {
  return useQuery({
    queryKey: ["category-over-time", category, year ?? "all", sign ?? "all"],
    enabled: !!category,
    queryFn: async () => {
      const { data } = await api.get<MonthTotal[]>("/dashboard/category-over-time", {
        params: {
          category,
          ...(year && year !== "All" ? { year } : {}),
          ...(sign ? { sign } : {}),
        },
      });
      return data;
    },
  });
}
