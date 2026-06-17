"use client";

import useSWR from "swr";
import { Topbar } from "@/components/Topbar";
import { ChartBar, ChartLine } from "@/components/Charts";
import { analyticsApi } from "@/lib/api";

export default function AnalyticsPage() {
  const { data, error, isLoading } = useSWR("analytics", () => analyticsApi.overview());
  const hasEmails = (data?.overview?.total_emails ?? 0) > 0;

  return (
    <>
      <Topbar title="Analytics" />
      <div className="p-6 space-y-4">
        {isLoading && <div className="text-sm text-slate-500">Loading analytics...</div>}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            Analytics could not be loaded. Please sign in again.
          </div>
        )}
        {!isLoading && !error && !hasEmails && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-soft">
            No email data yet. Add an email from Inbox to populate analytics.
          </div>
        )}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat label="Emails" value={data?.overview?.total_emails ?? 0} />
          <Stat label="Important" value={data?.overview?.total_important ?? 0} />
          <Stat label="Fraud" value={data?.overview?.total_fraud ?? 0} />
          <Stat label="Voice Notes" value={data?.overview?.voice_notes_sent ?? 0} />
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
          <h3 className="text-sm font-semibold mb-3">Volume (30 days)</h3>
          <ChartLine data={data?.timeline ?? []} />
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
          <h3 className="text-sm font-semibold mb-3">Scam Trend</h3>
          <ChartLine data={data?.scam_trend ?? []} />
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
          <h3 className="text-sm font-semibold mb-3">By Priority</h3>
          <ChartBar data={data?.by_priority ?? []} />
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
          <h3 className="text-sm font-semibold mb-3">Top Senders</h3>
          <ChartBar data={data?.by_sender ?? []} />
        </div>
        </div>
      </div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  );
}
