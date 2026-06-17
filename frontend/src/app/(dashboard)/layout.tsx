"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!isLoading || user) return;
    const id = window.setTimeout(() => router.replace("/login"), 2_000);
    return () => window.clearTimeout(id);
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen grid place-items-center text-slate-500">
        Authenticating…
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen grid place-items-center text-slate-500">
        Redirecting to login…
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <Sidebar onLogout={() => { logout(); router.push("/login"); }} />
      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  );
}
