/** Small utilities shared across components. */

export function classNames(...xs: (string | false | null | undefined)[]) {
  return xs.filter(Boolean).join(" ");
}

export function formatDate(iso: string | Date | undefined | null) {
  if (!iso) return "";
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return d.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function priorityColor(p: string) {
  switch (p) {
    case "critical":
      return "bg-red-100 text-red-700 border-red-200";
    case "high":
      return "bg-orange-100 text-orange-700 border-orange-200";
    case "medium":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    default:
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
  }
}

export function categoryColor(c: string) {
  const map: Record<string, string> = {
    banking: "bg-blue-100 text-blue-700",
    interview_calls: "bg-purple-100 text-purple-700",
    bills: "bg-pink-100 text-pink-700",
    security: "bg-rose-100 text-rose-700",
    job_alerts: "bg-indigo-100 text-indigo-700",
    orders: "bg-amber-100 text-amber-700",
    travel: "bg-teal-100 text-teal-700",
    shopping: "bg-lime-100 text-lime-700",
  };
  return map[c] ?? "bg-slate-100 text-slate-700";
}
