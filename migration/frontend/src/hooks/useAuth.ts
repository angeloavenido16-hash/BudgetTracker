import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Token } from "../api/types";

/** Is a JWT currently stored? (used to gate protected routes) */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem("token");
}

/** Clear the token and bounce to the login screen. */
export function logout() {
  localStorage.removeItem("token");
  window.location.href = "/login";
}

/** POST /auth/login — stores the JWT on success. */
export function useLogin() {
  return useMutation({
    mutationFn: async (creds: { username: string; password: string }) => {
      const { data } = await api.post<Token>("/auth/login", creds);
      return data;
    },
    onSuccess: (data) => {
      localStorage.setItem("token", data.access_token);
    },
  });
}
