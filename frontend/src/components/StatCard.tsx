"use client";

import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft">
      <div className="flex items-center gap-3">
        {icon && <div className="h-10 w-10 rounded-lg bg-brand-50 text-brand-700 grid place-items-center">{icon}</div>}
        <div>
          <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
          <div className="text-2xl font-semibold text-slate-900">{value}</div>
        </div>
      </div>
      {hint && <div className="mt-3 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}
