"use client";

import { useState } from "react";
import { Mail } from "lucide-react";

import { accountsApi } from "@/lib/api";

export function ConnectAccountButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function connect() {
    setLoading(true);
    setError(null);
    try {
      const start = await accountsApi.gmailStart();
      window.location.href = start.authorize_url;
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not connect Gmail.");
      setLoading(false);
    }
  }

  return (
    <div className="space-y-1">
      <button
        disabled={loading}
        onClick={connect}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-700 disabled:opacity-50"
      >
        <Mail size={16} />
        {loading ? "Connecting..." : "Connect Gmail"}
      </button>
      {error && <p className="max-w-64 text-xs text-red-600">{error}</p>}
    </div>
  );
}
