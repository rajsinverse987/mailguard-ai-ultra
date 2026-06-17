"use client";

import { Bell, Search } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function Topbar({ title }: { title: string }) {
  const [q, setQ] = useState("");
  const router = useRouter();
  return (
    <header className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-slate-200">
      <div className="px-6 py-4 flex items-center gap-4">
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">{title}</h1>
        <form
          className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
          onSubmit={(e) => {
            e.preventDefault();
            if (q.trim()) router.push(`/search?q=${encodeURIComponent(q)}`);
          }}
        >
          <Search size={16} className="text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search inbox semantically…"
            className="bg-transparent outline-none text-sm w-72"
          />
        </form>
        <button className="relative h-9 w-9 grid place-items-center rounded-lg hover:bg-slate-100">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
