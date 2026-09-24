/** Email Compose Form with visible AI typing animation effects. */
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/stores/uiStore";
import { useEmailStore } from "@/stores/emailStore";
import { api } from "@/lib/api";
import { Send, Trash2, Sparkles, ChevronDown, ChevronUp } from "lucide-react";

export const ComposeForm: React.FC = () => {
  const router = useRouter();
  const {
    composeDraft,
    updateDraftField,
    clearComposeDraft,
    activelyTypingField,
    isTypingAnimationActive,
  } = useUIStore();

  const { fetchEmails } = useEmailStore();

  const [showCcBcc, setShowCcBcc] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!composeDraft.to || composeDraft.to.length === 0 || !composeDraft.to[0]) {
      setErrorMessage("Please enter at least one recipient.");
      return;
    }
    if (!composeDraft.subject.trim()) {
      setErrorMessage("Please enter a subject.");
      return;
    }

    setIsSending(true);
    setErrorMessage(null);

    try {
      await api.sendEmail({
        to: composeDraft.to,
        cc: composeDraft.cc,
        bcc: composeDraft.bcc,
        subject: composeDraft.subject,
        body: composeDraft.body,
      });

      clearComposeDraft();
      await fetchEmails();
      router.push("/sent");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to send email.");
    } finally {
      setIsSending(false);
    }
  };

  const handleDiscard = () => {
    clearComposeDraft();
    router.push("/inbox");
  };

  return (
    <div className="max-w-4xl mx-auto bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-lg overflow-hidden flex flex-col h-[calc(100vh-140px)]">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50">
        <div className="flex items-center space-x-2">
          <h2 className="text-sm font-bold text-zinc-900 dark:text-zinc-100">New Message</h2>
          {isTypingAnimationActive && (
            <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 text-[10px] font-semibold animate-pulse">
              <Sparkles className="w-3 h-3" />
              <span>AI is populating this form...</span>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={() => setShowCcBcc(!showCcBcc)}
          className="text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 flex items-center space-x-1"
        >
          <span>{showCcBcc ? "Hide CC/BCC" : "Show CC/BCC"}</span>
          {showCcBcc ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div className="px-6 py-2 bg-rose-50 dark:bg-rose-950/40 border-b border-rose-200 text-xs text-rose-600 dark:text-rose-400">
          {errorMessage}
        </div>
      )}

      {/* Compose Form */}
      <form onSubmit={handleSend} className="flex-1 flex flex-col p-6 space-y-4 overflow-y-auto">
        {/* TO Field */}
        <div
          className={`flex items-center space-x-3 pb-2 border-b transition-all duration-300 ${
            activelyTypingField === "to"
              ? "border-blue-500 ring-2 ring-blue-500/20 rounded-md p-1.5 bg-blue-50/20 dark:bg-blue-950/20"
              : "border-zinc-200 dark:border-zinc-800"
          }`}
        >
          <span className="w-14 text-xs font-semibold text-zinc-500">To:</span>
          <input
            type="text"
            value={(composeDraft.to || []).join(", ")}
            onChange={(e) =>
              updateDraftField(
                "to",
                e.target.value.split(",").map((s) => s.trim())
              )
            }
            placeholder="recipient@example.com"
            className="flex-1 text-xs bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none"
          />
          {activelyTypingField === "to" && (
            <span className="w-2 h-4 bg-blue-500 animate-cursor-blink inline-block" />
          )}
        </div>

        {/* CC and BCC fields */}
        {showCcBcc && (
          <>
            <div className="flex items-center space-x-3 pb-2 border-b border-zinc-200 dark:border-zinc-800">
              <span className="w-14 text-xs font-semibold text-zinc-500">Cc:</span>
              <input
                type="text"
                value={(composeDraft.cc || []).join(", ")}
                onChange={(e) =>
                  updateDraftField(
                    "cc",
                    e.target.value.split(",").map((s) => s.trim())
                  )
                }
                placeholder="cc@example.com"
                className="flex-1 text-xs bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none"
              />
            </div>

            <div className="flex items-center space-x-3 pb-2 border-b border-zinc-200 dark:border-zinc-800">
              <span className="w-14 text-xs font-semibold text-zinc-500">Bcc:</span>
              <input
                type="text"
                value={(composeDraft.bcc || []).join(", ")}
                onChange={(e) =>
                  updateDraftField(
                    "bcc",
                    e.target.value.split(",").map((s) => s.trim())
                  )
                }
                placeholder="bcc@example.com"
                className="flex-1 text-xs bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none"
              />
            </div>
          </>
        )}

        {/* SUBJECT Field */}
        <div
          className={`flex items-center space-x-3 pb-2 border-b transition-all duration-300 ${
            activelyTypingField === "subject"
              ? "border-blue-500 ring-2 ring-blue-500/20 rounded-md p-1.5 bg-blue-50/20 dark:bg-blue-950/20"
              : "border-zinc-200 dark:border-zinc-800"
          }`}
        >
          <span className="w-14 text-xs font-semibold text-zinc-500">Subject:</span>
          <input
            type="text"
            value={composeDraft.subject || ""}
            onChange={(e) => updateDraftField("subject", e.target.value)}
            placeholder="Enter subject..."
            className="flex-1 text-xs bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none font-medium"
          />
          {activelyTypingField === "subject" && (
            <span className="w-2 h-4 bg-blue-500 animate-cursor-blink inline-block" />
          )}
        </div>

        {/* BODY Field */}
        <div
          className={`flex-1 flex flex-col rounded-xl transition-all duration-300 ${
            activelyTypingField === "body"
              ? "ring-2 ring-blue-500/30 p-2 bg-blue-50/10 dark:bg-blue-950/20"
              : ""
          }`}
        >
          <textarea
            value={composeDraft.body || ""}
            onChange={(e) => updateDraftField("body", e.target.value)}
            placeholder="Write your email here..."
            className="w-full flex-1 min-h-[220px] text-xs leading-relaxed bg-transparent text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none resize-none"
          />
          {activelyTypingField === "body" && (
            <div className="flex items-center space-x-1.5 text-[10px] text-blue-500 font-medium pt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping" />
              <span>AI typing body text...</span>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center space-x-3">
            <button
              type="submit"
              disabled={isSending}
              className="flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-md shadow-blue-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isSending ? "Sending..." : "Send Email"}</span>
            </button>
          </div>

          <button
            type="button"
            onClick={handleDiscard}
            className="p-2 text-zinc-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20 rounded-xl transition-colors"
            title="Discard Draft"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
