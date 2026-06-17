"use client";

import { useState } from "react";
import { Topbar } from "@/components/Topbar";
import { useAuth } from "@/hooks/useAuth";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({
    whatsapp_number: user?.whatsapp_number ?? "",
    preferred_language: user?.preferred_language ?? "hi",
    preferred_voice: user?.preferred_voice ?? "personal_assistant",
    voice_gender: user?.voice_gender ?? "female",
    morning_briefing_time: user?.morning_briefing_time ?? "08:00",
    enable_voice_alerts: user?.enable_voice_alerts ?? true,
    enable_text_alerts: user?.enable_text_alerts ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await authApi.updateMe(form);
      await refresh();
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Topbar title="Settings" />
      <div className="p-6 max-w-2xl">
        <form onSubmit={save} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-soft space-y-4">
          <Field label="WhatsApp number (E.164)">
            <input
              type="tel"
              value={form.whatsapp_number}
              onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
              placeholder="+91XXXXXXXXXX"
              className="input"
            />
          </Field>
          <Field label="Preferred language">
            <select
              value={form.preferred_language}
              onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}
              className="input"
            >
              <option value="hi">Hindi</option>
              <option value="en">English</option>
            </select>
          </Field>
          <Field label="Preferred voice">
            <select
              value={form.preferred_voice}
              onChange={(e) => setForm({ ...form, preferred_voice: e.target.value })}
              className="input"
            >
              <option value="personal_assistant">Personal Assistant</option>
              <option value="news_reader">News Reader</option>
              <option value="urgent_alert">Urgent Alert</option>
            </select>
          </Field>
          <Field label="Voice gender">
            <select
              value={form.voice_gender}
              onChange={(e) => setForm({ ...form, voice_gender: e.target.value })}
              className="input"
            >
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
          </Field>
          <Field label="Morning briefing time (HH:MM)">
            <input
              type="time"
              value={form.morning_briefing_time}
              onChange={(e) => setForm({ ...form, morning_briefing_time: e.target.value })}
              className="input"
            />
          </Field>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.enable_voice_alerts}
                onChange={(e) => setForm({ ...form, enable_voice_alerts: e.target.checked })}
              />
              Send voice notes on WhatsApp
            </label>
          </div>
          <div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.enable_text_alerts}
                onChange={(e) => setForm({ ...form, enable_text_alerts: e.target.checked })}
              />
              Send text summaries on WhatsApp
            </label>
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-brand-600 text-white disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
            {saved && <span className="text-sm text-emerald-600">Saved</span>}
          </div>
        </form>
      </div>
      <style jsx global>{`
        .input { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; outline: none; }
        .input:focus { border-color: #2563eb; }
      `}</style>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="text-xs font-medium text-slate-700 mb-1">{label}</div>
      {children}
    </label>
  );
}
