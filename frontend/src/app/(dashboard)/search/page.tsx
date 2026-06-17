"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { Topbar } from "@/components/Topbar";
import { EmailCard } from "@/components/EmailCard";
import { emailsApi } from "@/lib/api";
import type { EmailSummary } from "@/types";

type SearchResult = {
  email: EmailSummary;
  score: number;
};

function SearchInner() {
  const params = useSearchParams();
  const initial = params.get("q") ?? "";
  const [q, setQ] = useState(initial);
  const searchTerm = q.trim();
  const canSearch = searchTerm.length >= 2;
  const { data, isLoading, isValidating } = useSWR<SearchResult[]>(
    canSearch ? `semantic-search:${searchTerm}` : null,
    () => emailsApi.semantic(searchTerm)
  );

  const results = canSearch ? data ?? [] : [];
  const busy = canSearch && (isLoading || isValidating);

  return (
    <>
      <Topbar title="Semantic Search" />
      <div className="p-6 space-y-4">
        <input
          autoFocus
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Try: invoices, Microsoft interview, banking alerts…"
          className="w-full px-4 py-3 rounded-xl border border-slate-200 text-base outline-none focus:border-brand-500"
        />
        {busy && <div className="text-slate-500">Searching…</div>}
        <div className="space-y-3">
          {results.map((r) => (
            <div key={r.email.id} className="space-y-1">
              <EmailCard email={r.email} />
              <div className="text-xs text-slate-500 pl-4">Relevance: {(r.score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading…</div>}>
      <SearchInner />
    </Suspense>
  );
}
