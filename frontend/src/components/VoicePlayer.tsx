"use client";

import { useState } from "react";
import { Volume2 } from "lucide-react";

export function VoicePlayer({
  src,
  text,
}: {
  src?: string | null;
  text: string;
}) {
  const [speaking, setSpeaking] = useState(false);

  function speakText() {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }

  return (
    <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl p-3">
      <Volume2 className="text-brand-600" />
      <div className="flex-1 min-w-0">
        <div className="text-xs text-slate-500 truncate">{text}</div>
        {src ? (
          <audio controls src={src} className="w-full mt-1" />
        ) : (
          <button
            type="button"
            onClick={speakText}
            className="mt-2 inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            <Volume2 size={14} />
            {speaking ? "Speaking..." : "Speak"}
          </button>
        )}
      </div>
    </div>
  );
}
