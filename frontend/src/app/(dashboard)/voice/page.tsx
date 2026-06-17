"use client";

import { useState } from "react";
import useSWR from "swr";
import { Loader2, Volume2 } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { VoicePlayer } from "@/components/VoicePlayer";
import { notificationsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function VoicePage() {
  const { data, mutate } = useSWR("voice-notes", () => notificationsApi.voiceNotes());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generateLatest() {
    setBusy(true);
    setError(null);
    try {
      await notificationsApi.generateLatestVoice();
      await mutate();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Voice note could not be generated.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Topbar title="Voice Notifications" />
      <div className="p-6 space-y-3">
        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={generateLatest}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? <Loader2 size={16} className="animate-spin" /> : <Volume2 size={16} />}
            {busy ? "Generating..." : "Generate latest"}
          </button>
        </div>
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {(data ?? []).length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center text-slate-500">
            No voice notes generated yet. Add an email first, then generate the latest note.
          </div>
        )}
        {(data ?? []).map((v: any) => (
          <div key={v.id} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-soft">
            <div className="flex items-center gap-2 mb-2">
              <Volume2 className="text-brand-600" size={18} />
              <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 uppercase">{v.engine}</span>
              <span className="text-xs text-slate-500">{v.voice}</span>
              <span className="ml-auto text-xs text-slate-500">{formatDate(v.created_at)}</span>
            </div>
            <VoicePlayer src={v.audio_url} text={v.text} />
          </div>
        ))}
      </div>
    </>
  );
}
