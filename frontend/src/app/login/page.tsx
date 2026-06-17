"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/overview");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-brand-50 to-slate-100 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-soft p-8 border border-slate-200">
        <div className="flex items-center gap-2 mb-6">
          <div className="h-10 w-10 rounded-xl bg-brand-600 grid place-items-center font-bold text-white">
            M
          </div>
          <div>
            <div className="font-semibold text-lg">MailGuard AI Ultra</div>
            <div className="text-xs text-slate-500">Sign in to your dashboard</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none"
            required
          />
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button
            disabled={busy}
            className="w-full py-2 rounded-lg bg-brand-600 text-white font-medium disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="text-xs text-slate-500 mt-4 text-center">
          New here? <Link className="text-brand-600" href="/register">Create an account</Link>
        </div>
      </div>
    </div>
  );
}
