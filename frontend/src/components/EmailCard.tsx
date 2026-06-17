"use client";

import Link from "next/link";
import { ShieldAlert } from "lucide-react";
import type { EmailSummary } from "@/types";
import { categoryColor, formatDate, priorityColor } from "@/lib/utils";
import { CategoryBadge } from "./CategoryBadge";

export function EmailCard({ email }: { email: EmailSummary }) {
  const sender = email.sender_company || email.sender_name || email.sender_email;
  return (
    <Link
      href={`/inbox/${email.id}`}
      className="block bg-white border border-slate-200 hover:border-brand-500 transition-colors rounded-xl p-4 shadow-soft"
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-md border ${priorityColor(email.priority)}`}>
              {email.priority.toUpperCase()}
            </span>
            <CategoryBadge value={email.category} />
            {email.is_phishing && (
              <span className="text-xs px-2 py-0.5 rounded-md bg-red-100 text-red-700 border border-red-200 flex items-center gap-1">
                <ShieldAlert size={12} /> Phishing · {Math.round(email.threat_score)}
              </span>
            )}
            <span className="ml-auto text-xs text-slate-500">{formatDate(email.received_at)}</span>
          </div>
          <div className="mt-2 font-semibold text-slate-900 truncate">{email.subject}</div>
          <div className="text-xs text-slate-500 truncate">{sender}</div>
          {email.summary && (
            <p className="mt-2 text-sm text-slate-700 line-clamp-2">{email.summary}</p>
          )}
        </div>
      </div>
    </Link>
  );
}
