"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", phone: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register(form);
      router.push("/overview");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-brand-50 to-slate-100 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-soft p-8 border border-slate-200">
        <h1 className="text-xl font-semibold mb-1">Create your account</h1>
        <p className="text-xs text-slate-500 mb-6">Start monitoring your inbox with AI.</p>
        <form onSubmit={submit} className="space-y-3">
          {(["full_name", "email", "password", "phone"] as const).map((k) => (
            <input
              key={k}
              type={k === "email" ? "email" : k === "password" ? "password" : "text"}
              placeholder={k.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              value={(form as any)[k]}
              onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              required={k !== "phone"}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none"
            />
          ))}
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button
            disabled={busy}
            className="w-full py-2 rounded-lg bg-brand-600 text-white font-medium disabled:opacity-50"
          >
            {busy ? "Creating…" : "Create account"}
          </button>
        </form>
        <div className="text-xs text-slate-500 mt-4 text-center">
          Already have an account? <Link className="text-brand-600" href="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
