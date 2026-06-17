"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Inbox,
  Sparkles,
  Volume2,
  MessageSquare,
  Shield,
  BarChart3,
  Search,
  Settings,
  LogOut,
} from "lucide-react";

import { classNames } from "@/lib/utils";

const items = [
  { href: "/overview", label: "Overview", Icon: LayoutDashboard },
  { href: "/inbox", label: "Inbox Intelligence", Icon: Inbox },
  { href: "/assistant", label: "AI Assistant", Icon: Sparkles },
  { href: "/voice", label: "Voice Notifications", Icon: Volume2 },
  { href: "/whatsapp", label: "WhatsApp Logs", Icon: MessageSquare },
  { href: "/fraud", label: "Fraud Center", Icon: Shield },
  { href: "/analytics", label: "Analytics", Icon: BarChart3 },
  { href: "/search", label: "Search", Icon: Search },
  { href: "/settings", label: "Settings", Icon: Settings },
];

export function Sidebar({ onLogout }: { onLogout?: () => void }) {
  const pathname = usePathname() || "";
  return (
    <aside className="hidden md:flex md:w-64 md:flex-col bg-ink-900 text-slate-100">
      <div className="px-6 py-6 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-lg bg-brand-600 grid place-items-center font-bold">
            M
          </div>
          <div>
            <div className="font-semibold tracking-wide">MailGuard</div>
            <div className="text-xs text-slate-400">AI Ultra</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map(({ href, label, Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={classNames(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-white/10 text-white"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              )}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-3 border-t border-white/5">
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 hover:text-white"
        >
          <LogOut size={18} /> Logout
        </button>
      </div>
    </aside>
  );
}
