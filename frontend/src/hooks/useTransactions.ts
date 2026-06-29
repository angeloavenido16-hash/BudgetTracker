import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Transaction } from "../api/types";

/** GET /transactions — list, optionally filtered by fund. */
export function useTransactions(fundId?: number) {
  return useQuery({
    queryKey: ["transactions", fundId ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<Transaction[]>("/transactions", {
        params: fundId ? { fund_id: fundId } : undefined,
      });
      return data;
    },
  });
}

/** POST /transactions — create, then invalidate dependent caches. */
export function useCreateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Transaction>) => {
      const { data } = await api.post<Transaction>("/transactions", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["fund-summaries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/** PUT /transactions/{id} — update (category/amount/date/remarks; fund fixed). */
export function useUpdateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: Partial<Transaction> & { id: number }) => {
      const { data } = await api.put<Transaction>(`/transactions/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["fund-summaries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/** DELETE /transactions/{id} — remove, then invalidate dependent caches. */
export function useDeleteTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/transactions/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["fund-summaries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
