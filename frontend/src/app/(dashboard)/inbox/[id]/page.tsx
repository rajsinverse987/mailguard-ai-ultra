"use client";

import { use } from "react";
import useSWR from "swr";
import { Topbar } from "@/components/Topbar";
import { PriorityBadge } from "@/components/PriorityBadge";
import { CategoryBadge } from "@/components/CategoryBadge";
import { ThreatMeter } from "@/components/ThreatMeter";
import { emailsApi, notificationsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function EmailDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: email } = useSWR(["email", id], () => emailsApi.get(id));
  const { data: voice } = useSWR("voice", () => notificationsApi.voiceNotes());

  if (!email) return <div className="p-6">Loading…</div>;

  const sender = email.sender_company || email.sender_name || email.sender_email;
  const relatedVoice = (voice ?? []).filter((v: any) => v.email_id === id);

  return (
    <>
      <Topbar title={email.subject} />
      <div className="p-6 grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <PriorityBadge value={email.priority} />
            <CategoryBadge value={email.category} />
            {email.is_phishing && (
              <span className="text-xs px-2 py-0.5 rounded-md bg-red-100 text-red-700 border border-red-200">
                Phishing · {Math.round(email.threat_score)}
              </span>
            )}
            <span className="ml-auto text-xs text-slate-500">{formatDate(email.received_at)}</span>
          </div>
          <div>
            <div className="text-xs text-slate-500">From</div>
            <div className="text-sm font-medium">{sender}</div>
          </div>
          {email.summary && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Summary</div>
              <p className="text-sm text-slate-800">{email.summary}</p>
            </div>
          )}
          {email.summary_hi && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Hindi Summary</div>
              <p className="text-sm text-slate-800">{email.summary_hi}</p>
            </div>
          )}
          {email.threat_reason && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Threat Analysis</div>
              <ThreatMeter score={email.threat_score} />
              <p className="text-sm text-slate-700 mt-2">{email.threat_reason}</p>
            </div>
          )}
          <hr />
          <pre className="whitespace-pre-wrap text-sm text-slate-700 font-sans">
            {email.body_text}
          </pre>
        </div>

        <aside className="space-y-3">
          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
            <h3 className="text-sm font-semibold mb-2">Voice Notes</h3>
            {relatedVoice.length === 0 && (
              <p className="text-xs text-slate-500">No voice notes generated for this email.</p>
            )}
            {relatedVoice.map((v: any) => (
              <div key={v.id} className="text-xs mt-2">
                <div className="text-slate-700">{v.text}</div>
                <div className="text-slate-400">{v.engine} · {v.voice}</div>
              </div>
            ))}
          </div>
          {email.action_items?.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
              <h3 className="text-sm font-semibold mb-2">Action Items</h3>
              <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
                {email.action_items.map((a: string, i: number) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
          {email.due_dates?.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
              <h3 className="text-sm font-semibold mb-2">Deadlines</h3>
              <ul className="text-sm text-slate-700 space-y-1">
                {email.due_dates.map((d: string, i: number) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </>
  );
}
