import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

/** GET /categories — sorted list of active expense category names. */
export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { data } = await api.get<string[]>("/categories");
      return data;
    },
  });
}

/** POST /categories — idempotent add, then refresh the list. */
export function useAddCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (name: string) => {
      await api.post("/categories", { name });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}
