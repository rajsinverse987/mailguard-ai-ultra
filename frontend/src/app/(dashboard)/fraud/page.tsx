"use client";

import useSWR from "swr";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { ThreatMeter } from "@/components/ThreatMeter";
import { fraudApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function FraudPage() {
  const { data } = useSWR("fraud-alerts", () => fraudApi.alerts());

  return (
    <>
      <Topbar title="Fraud Detection Center" />
      <div className="p-6 space-y-3">
        {(data ?? []).length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center text-slate-500 flex flex-col items-center gap-2">
            <ShieldCheck size={28} className="text-emerald-600" />
            No phishing or scam alerts detected.
          </div>
        )}
        {(data ?? []).map((a: any) => (
          <div key={a.id} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
            <div className="flex items-center gap-2">
              <ShieldAlert className="text-rose-600" />
              <span className="text-xs px-2 py-0.5 rounded-md bg-rose-100 text-rose-700 uppercase">
                {a.severity}
              </span>
              <span className="text-xs text-slate-500">{formatDate(a.created_at)}</span>
              <span className="ml-auto text-xs text-slate-700 font-semibold">
                Threat Score: {Math.round(a.threat_score)}/100
              </span>
            </div>
            <div className="mt-2"><ThreatMeter score={a.threat_score} /></div>
            {a.reasoning && <p className="mt-2 text-sm text-slate-700">{a.reasoning}</p>}
            {a.reasons?.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-xs text-slate-600">
                {a.reasons.map((r: string, i: number) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
            {a.suspicious_links?.length > 0 && (
              <div className="mt-2 text-xs text-slate-500">
                <span className="font-semibold">Suspicious links:</span>{" "}
                {a.suspicious_links.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
