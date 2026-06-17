"use client";

import useSWR from "swr";
import { Sparkles, ShieldAlert, Inbox, Banknote, Volume2, MessageSquare } from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { StatCard } from "@/components/StatCard";
import { ChartLine, ChartPie } from "@/components/Charts";
import { analyticsApi, briefingsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function OverviewPage() {
  const { data } = useSWR("overview", () => analyticsApi.overview());
  const { data: briefings } = useSWR("briefings", () => briefingsApi.list());

  async function triggerMorning() {
    await briefingsApi.triggerMorning();
  }
  async function triggerEvening() {
    await briefingsApi.triggerEvening();
  }

  const overview = data?.overview;

  return (
    <>
      <Topbar title="Overview" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Emails" value={overview?.total_emails ?? "—"} icon={<Inbox size={18} />} />
          <StatCard label="Important" value={overview?.total_important ?? "—"} icon={<Sparkles size={18} />} hint="High + Critical" />
          <StatCard label="Phishing Blocked" value={overview?.total_fraud ?? "—"} icon={<ShieldAlert size={18} />} />
          <StatCard label="Interviews" value={overview?.total_interviews ?? "—"} icon={<MessageSquare size={18} />} />
          <StatCard label="Banking Alerts" value={overview?.total_banking ?? "—"} icon={<Banknote size={18} />} />
          <StatCard label="Voice Notes Sent" value={overview?.voice_notes_sent ?? "—"} icon={<Volume2 size={18} />} />
          <StatCard label="WhatsApp Sent" value={overview?.whatsapp_sent ?? "—"} icon={<MessageSquare size={18} />} />
          <StatCard label="Unread" value={overview?.total_unread ?? "—"} icon={<Inbox size={18} />} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft lg:col-span-2">
            <h3 className="text-sm font-semibold mb-3">Email Volume (30 days)</h3>
            <ChartLine data={data?.timeline ?? []} />
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
            <h3 className="text-sm font-semibold mb-3">Category Mix</h3>
            <ChartPie data={data?.by_category ?? []} />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-semibold">Daily Briefings</h3>
            <button
              onClick={triggerMorning}
              className="ml-auto px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs hover:bg-brand-700"
            >
              Send Morning Briefing
            </button>
            <button
              onClick={triggerEvening}
              className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs hover:bg-slate-800"
            >
              Send Evening Summary
            </button>
          </div>
          <div className="divide-y">
            {(briefings ?? []).slice(0, 5).map((b: any) => (
              <div key={b.id} className="py-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 capitalize">{b.kind}</span>
                  <span className="text-xs text-slate-500">{formatDate(b.created_at)}</span>
                  <span className={`ml-auto text-xs ${b.delivered ? "text-emerald-600" : "text-slate-400"}`}>
                    {b.delivered ? "delivered" : "pending"}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-700">{b.text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
