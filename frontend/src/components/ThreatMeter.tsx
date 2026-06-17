"use client";

export function ThreatMeter({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const color =
    pct >= 85 ? "bg-red-600" : pct >= 60 ? "bg-orange-500" : pct >= 30 ? "bg-yellow-500" : "bg-emerald-500";
  return (
    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
      <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
