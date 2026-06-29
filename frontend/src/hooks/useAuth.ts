import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Token } from "../api/types";

export interface UserInfo {
  id: number;
  username: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string | null;
}

export interface MeResponse {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string | null;
}

/** Is a JWT currently stored? (used to gate protected routes) */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem("token");
}

/** Clear the token and bounce to the login screen. */
export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/login";
}

/** Decode JWT payload without verification (already verified server-side). */
function decodeToken(token: string): Record<string, unknown> {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch {
    return {};
  }
}

/** GET /auth/me — current user profile. */
function useMeQuery() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await api.get<MeResponse>("/auth/me");
      return data;
    },
    enabled: isAuthenticated(),
    staleTime: 5 * 60_000,
  });
}

/** Stored user info from localStorage. */
function storedUser(): UserInfo | null {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/** Full current-user info from cache or localStorage fallback. */
export function useCurrentUser(): UserInfo | null {
  const { data } = useMeQuery();
  return data
    ? { ...data, is_active: true }
    : storedUser();
}

/** POST /auth/login — stores the JWT + user info on success. */
export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (creds: { username: string; password: string }) => {
      const { data } = await api.post<Token>("/auth/login", creds);
      return data;
    },
    onSuccess: (data) => {
      localStorage.setItem("token", data.access_token);
      // Decode token to get user identity immediately
      const payload = decodeToken(data.access_token);
      const info: UserInfo = {
        id: Number(payload.sub ?? 0),
        username: "",
        is_admin: !!payload.is_admin,
        is_active: true,
        created_at: null,
      };
      localStorage.setItem("user", JSON.stringify(info));
      qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

/** POST /auth/register — create a new user account. */
export function useRegister() {
  return useMutation({
    mutationFn: async (creds: { username: string; password: string }) => {
      const { data } = await api.post("/auth/register", creds);
      return data as { username: string };
    },
  });
}

/** GET /auth/users — list all users (admin only). */
export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const { data } = await api.get<UserInfo[]>("/auth/users");
      return data;
    },
    enabled: isAuthenticated(),
  });
}

/** DELETE /auth/users/:id */
export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: number) => {
      await api.delete(`/auth/users/${userId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

/** PATCH /auth/users/:id/deactivate */
export function useDeactivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: number) => {
      const { data } = await api.patch<UserInfo>(
        `/auth/users/${userId}/deactivate`,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

/** PATCH /auth/users/:id/activate */
export function useActivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: number) => {
      const { data } = await api.patch<UserInfo>(
        `/auth/users/${userId}/activate`,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

/** PATCH /auth/users/:id/password */
export function useResetPassword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      userId,
      password,
    }: {
      userId: number;
      password: string;
    }) => {
      const { data } = await api.patch(`/auth/users/${userId}/password`, {
        password,
      });
      return data as { username: string };
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}
