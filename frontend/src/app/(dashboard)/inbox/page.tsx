"use client";

import { type FormEvent, useState } from "react";
import { Loader2, MailPlus } from "lucide-react";
import useSWR from "swr";

import { Topbar } from "@/components/Topbar";
import { EmailCard } from "@/components/EmailCard";
import { useEmails } from "@/hooks/useEmails";
import { accountsApi, emailsApi } from "@/lib/api";
import { ConnectAccountButton } from "@/components/ConnectAccountButton";

const CATEGORIES = [
  "banking", "bills", "interview_calls", "job_alerts", "orders",
  "shopping", "travel", "personal", "security", "other",
];

export default function InboxPage() {
  const [filters, setFilters] = useState<{ category?: string; priority?: string; search?: string }>({});
  const [manualEmail, setManualEmail] = useState({
    sender_email: "",
    sender_name: "",
    subject: "",
    body_text: "",
  });
  const [manualBusy, setManualBusy] = useState(false);
  const [manualStatus, setManualStatus] = useState<{
    kind: "success" | "error";
    message: string;
  } | null>(null);
  const { data, isLoading, mutate: refreshEmails } = useEmails({ page: 1, size: 50, ...filters });
  const { data: accounts, mutate: refreshAccounts } = useSWR("accounts", () => accountsApi.list());

  async function submitManualEmail(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setManualBusy(true);
    setManualStatus(null);
    try {
      await emailsApi.createManual({
        ...manualEmail,
        sender_name: manualEmail.sender_name || undefined,
      });
      setManualEmail({ sender_email: "", sender_name: "", subject: "", body_text: "" });
      await Promise.all([refreshEmails(), refreshAccounts()]);
      setManualStatus({ kind: "success", message: "Email added." });
    } catch (err: any) {
      setManualStatus({
        kind: "error",
        message: err?.response?.data?.detail || "Email could not be added.",
      });
    } finally {
      setManualBusy(false);
    }
  }

  return (
    <>
      <Topbar title="Inbox Intelligence" />
      <div className="p-6 space-y-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
          <div className="flex items-center gap-2 flex-wrap">
            <input
              placeholder="Search subject…"
              value={filters.search ?? ""}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm w-64"
            />
            <select
              value={filters.priority ?? ""}
              onChange={(e) => setFilters({ ...filters, priority: e.target.value || undefined })}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              <option value="">All priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={filters.category ?? ""}
              onChange={(e) => setFilters({ ...filters, category: e.target.value || undefined })}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              <option value="">All categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c.replace("_", " ")}</option>
              ))}
            </select>
            <div className="ml-auto flex items-center gap-2">
              <ConnectAccountButton />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
          <div className="space-y-3">
            {isLoading && <div className="text-slate-500">Loading…</div>}
            {(data?.items ?? []).map((e: any) => (
              <EmailCard key={e.id} email={e} />
            ))}
            {!isLoading && (data?.items ?? []).length === 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center text-slate-500">
                No emails match your filters yet.
              </div>
            )}
          </div>

          <aside className="space-y-3">
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
              <div className="flex items-center gap-2 mb-3">
                <MailPlus size={16} className="text-brand-600" />
                <h3 className="text-sm font-semibold">Add Email</h3>
              </div>
              <form onSubmit={submitManualEmail} className="space-y-2">
                <input
                  type="email"
                  required
                  placeholder="Sender email"
                  value={manualEmail.sender_email}
                  onChange={(e) =>
                    setManualEmail({ ...manualEmail, sender_email: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-brand-500 outline-none"
                />
                <input
                  placeholder="Sender name"
                  value={manualEmail.sender_name}
                  onChange={(e) =>
                    setManualEmail({ ...manualEmail, sender_name: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-brand-500 outline-none"
                />
                <input
                  required
                  placeholder="Subject"
                  value={manualEmail.subject}
                  onChange={(e) => setManualEmail({ ...manualEmail, subject: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-brand-500 outline-none"
                />
                <textarea
                  required
                  rows={5}
                  placeholder="Email body"
                  value={manualEmail.body_text}
                  onChange={(e) =>
                    setManualEmail({ ...manualEmail, body_text: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-brand-500 outline-none resize-y"
                />
                <button
                  disabled={manualBusy}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
                >
                  {manualBusy ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <MailPlus size={16} />
                  )}
                  {manualBusy ? "Adding..." : "Add email"}
                </button>
                {manualStatus && (
                  <p
                    className={`text-xs ${
                      manualStatus.kind === "success" ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    {manualStatus.message}
                  </p>
                )}
              </form>
            </div>
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
              <h3 className="text-sm font-semibold mb-2">Connected Accounts</h3>
              {(accounts ?? []).length === 0 && (
                <p className="text-xs text-slate-500">No accounts connected. Connect Gmail above.</p>
              )}
              <ul className="space-y-2">
                {(accounts ?? []).map((a: any) => (
                  <li key={a.id} className="flex items-center gap-2 text-sm">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    <span className="font-medium">{a.provider}</span>
                    <span className="text-slate-500 truncate">{a.email_address}</span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </>
  );
}
