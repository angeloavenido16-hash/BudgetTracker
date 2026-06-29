import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Fund, FundSummary } from "../api/types";

/** GET /funds — list income funds, optionally filtered by type. */
export function useFunds(fundType?: string) {
  return useQuery({
    queryKey: ["funds", fundType ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<Fund[]>("/funds", {
        params: fundType ? { fund_type: fundType } : undefined,
      });
      return data;
    },
  });
}

/** GET /funds/summaries — bulk per-fund summaries keyed by fund id. */
export function useFundSummaries() {
  return useQuery({
    queryKey: ["fund-summaries"],
    queryFn: async () => {
      const { data } = await api.get<Record<number, FundSummary>>(
        "/funds/summaries"
      );
      return data;
    },
  });
}

/** POST /funds — create a fund, then invalidate caches. */
export function useCreateFund() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Fund>) => {
      const { data } = await api.post<Fund>("/funds", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["funds"] });
      qc.invalidateQueries({ queryKey: ["fund-summaries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/** PUT /funds/{id} — update a fund, then invalidate caches. */
export function useUpdateFund() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: Partial<Fund> & { id: number }) => {
      const { data } = await api.put<Fund>(`/funds/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["funds"] });
      qc.invalidateQueries({ queryKey: ["fund-summaries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/** DELETE /funds/{id} — remove a fund (cascades its txns), then invalidate. */
export function useDeleteFund() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/funds/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["funds"] });
      qc.invalidateQueries({ queryKey: ["fund-summaries"] });
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
