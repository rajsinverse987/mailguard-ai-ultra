"use client";

import useSWR from "swr";
import { emailsApi } from "@/lib/api";

export function useEmails(params: {
  page?: number;
  size?: number;
  category?: string;
  priority?: string;
  search?: string;
}) {
  return useSWR(["emails", params], () => emailsApi.list(params));
}

export function useEmail(id: string | null) {
  return useSWR(id ? ["email", id] : null, () => emailsApi.get(id!));
}

export function useSemanticSearch(query: string) {
  return useSWR(query.length >= 2 ? ["search", query] : null, () =>
    emailsApi.semantic(query)
  );
}
