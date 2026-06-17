"use client";

import { useSyncExternalStore } from "react";
import useSWR from "swr";

import { auth } from "@/lib/auth";
import { authApi } from "@/lib/api";
import type { User } from "@/types";

export function useAuth() {
  const hydrated = useSyncExternalStore(
    (callback) => {
      const id = window.setTimeout(callback, 0);
      return () => window.clearTimeout(id);
    },
    () => true,
    () => false
  );

  const hasToken = hydrated && auth.isLoggedIn();

  const fetcher = async () => {
    if (!auth.getToken()) return null;
    try {
      return await authApi.me();
    } catch {
      auth.clear();
      return null;
    }
  };

  const { data, mutate, isLoading, error } = useSWR<User | null>(
    hasToken ? "/auth/me" : null,
    fetcher,
    {
      shouldRetryOnError: false,
      revalidateOnFocus: false,
    }
  );

  return {
    user: data,
    isLoading: hydrated ? hasToken && isLoading : true,
    error,
    refresh: () => mutate(),
    login: async (email: string, password: string) => {
      const r = await authApi.login({ email, password });
      auth.setToken(r.access_token);
      await mutate();
      return r;
    },
    register: async (payload: {
      email: string;
      password: string;
      full_name: string;
      phone?: string;
    }) => {
      const user = await authApi.register(payload);
      const r = await authApi.login({
        email: payload.email,
        password: payload.password,
      });
      auth.setToken(r.access_token);
      await mutate(user, false);
      return user;
    },
    logout: () => {
      auth.clear();
      mutate(undefined, false);
    },
  };
}
