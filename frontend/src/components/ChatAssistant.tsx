"use client";

import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { assistantApi } from "@/lib/api";

type Citation = {
  email: {
    id: string;
    subject: string;
    sender_email: string;
    sender_company?: string | null;
    summary?: string | null;
    priority: string;
  };
  score: number;
};

export function ChatAssistant() {
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string; citations?: Citation[] }[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [voice, setVoice] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userMsg = { role: "user" as const, text: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);
    try {
      const r = await assistantApi.chat({ query: userMsg.text, voice_reply: voice });
      setMessages((m) => [
        ...m,
        {
          role: "ai",
          text: r.answer,
          citations: (r.cited_emails || []).map((e: any) => ({ email: e, score: 1 })),
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "ai", text: "Sorry — I couldn't reach the assistant right now." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-soft flex flex-col h-[70vh]">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 mt-10">
            <Sparkles className="mx-auto mb-2" />
            Ask me anything about your inbox.
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
              m.role === "user"
                ? "ml-auto bg-brand-600 text-white"
                : "mr-auto bg-slate-100 text-slate-900"
            }`}
          >
            <div className="whitespace-pre-wrap">{m.text}</div>
            {m.citations && m.citations.length > 0 && (
              <div className="mt-2 text-xs text-slate-500">
                <div className="font-semibold mb-1">Sources:</div>
                {m.citations.slice(0, 3).map((c, j) => (
                  <div key={j} className="truncate">
                    • {c.email.subject} — {c.email.sender_company || c.email.sender_email}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="border-t border-slate-200 p-3 flex items-center gap-2">
        <label className="text-xs flex items-center gap-1 text-slate-600">
          <input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} />
          Voice reply
        </label>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Any interview invitations? Banking alerts? Bills due?"
          className="flex-1 px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-brand-500"
        />
        <button
          disabled={busy}
          onClick={send}
          className="h-9 w-9 grid place-items-center rounded-lg bg-brand-600 text-white disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
