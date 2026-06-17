"use client";

import { useState } from "react";
import useSWR from "swr";
import { Loader2, MessageSquare, Send } from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { notificationsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function WhatsAppLogsPage() {
  const { data, mutate } = useSWR("notifications", () => notificationsApi.list());
  const { data: status } = useSWR("whatsapp-status", () =>
    notificationsApi.whatsappStatus()
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function sendLatest() {
    setBusy(true);
    setError(null);
    try {
      await notificationsApi.sendLatestWhatsApp();
      await mutate();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "WhatsApp notification could not be created.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Topbar title="WhatsApp Logs" />
      <div className="p-6 space-y-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex flex-wrap items-start gap-3">
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold">WhatsApp Status</h2>
              <p className="mt-1 text-sm text-slate-600">
                Provider: <span className="font-medium">{status?.provider ?? "meta"}</span>
                {status?.target_number ? ` - To: ${status.target_number}` : ""}
              </p>
              {status && !status.configured && (
                <p className="mt-2 text-sm text-red-600">
                  Missing {status.missing.join(", ")}. A log can still be created, but
                  real WhatsApp delivery needs these credentials.
                </p>
              )}
              {status && !status.has_target_number && (
                <p className="mt-2 text-sm text-red-600">
                  Add a phone or WhatsApp number in Settings before sending.
                </p>
              )}
              {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
            </div>
            <button
              type="button"
              onClick={sendLatest}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {busy ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {busy ? "Sending..." : "Send latest email"}
            </button>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="p-3">Channel</th>
                <th className="p-3">To</th>
                <th className="p-3">Provider</th>
                <th className="p-3">Status</th>
                <th className="p-3">Created</th>
                <th className="p-3">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {(data ?? []).map((n: any) => (
                <tr key={n.id}>
                  <td className="p-3 flex items-center gap-2">
                    <MessageSquare size={14} className="text-emerald-600" />
                    {n.channel}
                  </td>
                  <td className="p-3">{n.to_number}</td>
                  <td className="p-3">{n.provider}</td>
                  <td className="p-3">
                    <span
                      className={`rounded-md px-2 py-0.5 text-xs ${
                        n.delivered
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-rose-100 text-rose-700"
                      }`}
                    >
                      {n.delivered ? "delivered" : n.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-500">{formatDate(n.created_at)}</td>
                  <td className="p-3 max-w-xs truncate text-rose-600">{n.error || "-"}</td>
                </tr>
              ))}
              {(data ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="p-10 text-center text-slate-500">
                    No notifications yet. Use Send latest email to create the first log.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
