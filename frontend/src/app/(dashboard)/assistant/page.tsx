"use client";

import { Topbar } from "@/components/Topbar";
import { ChatAssistant } from "@/components/ChatAssistant";

export default function AssistantPage() {
  return (
    <>
      <Topbar title="AI Assistant" />
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <p className="text-sm text-slate-500 mb-4">
            Ask questions about your inbox in English or Hindi. Replies can be spoken aloud.
          </p>
          <ChatAssistant />
        </div>
      </div>
    </>
  );
}
