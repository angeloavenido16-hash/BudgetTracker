import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { BpiBalance } from "../api/types";

/** GET /bpi-balance — latest recorded bank balance. */
export function useBpiBalance() {
  return useQuery({
    queryKey: ["bpi-balance"],
    queryFn: async () => {
      const { data } = await api.get<BpiBalance>("/bpi-balance");
      return data;
    },
  });
}

/** PUT /bpi-balance — record a new balance, then refresh balance + dashboard. */
export function useSetBpiBalance() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (balance: number) => {
      const { data } = await api.put<BpiBalance>("/bpi-balance", { balance });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bpi-balance"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
