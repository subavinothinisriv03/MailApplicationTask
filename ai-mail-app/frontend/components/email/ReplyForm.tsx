/** Inline Reply Form attached to an opened email thread. */
"use client";

import React, { useState } from "react";
import { Email } from "@/lib/types";
import { api } from "@/lib/api";
import { useEmailStore } from "@/stores/emailStore";
import { Send, X, CornerUpLeft } from "lucide-react";

interface Props {
  email: Email;
  onClose?: () => void;
}

export const ReplyForm: React.FC<Props> = ({ email, onClose }) => {
  const [replyBody, setReplyBody] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { fetchEmails } = useEmailStore();

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyBody.trim()) return;

    setIsSending(true);
    setError(null);

    try {
      await api.replyToEmail(email.id, replyBody.trim());
      setReplyBody("");
      await fetchEmails();
      if (onClose) onClose();
    } catch (err: any) {
      setError(err.message || "Failed to send reply.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="mt-6 p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700/60 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="flex items-center justify-between mb-3 text-xs text-zinc-500">
        <div className="flex items-center space-x-2">
          <CornerUpLeft className="w-3.5 h-3.5 text-blue-500" />
          <span>
            Replying to <strong className="text-zinc-800 dark:text-zinc-200">{email.sender}</strong>
          </span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded-md"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {error && <div className="mb-2 text-xs text-rose-500">{error}</div>}

      <form onSubmit={handleSendReply}>
        <textarea
          value={replyBody}
          onChange={(e) => setReplyBody(e.target.value)}
          placeholder="Write your reply..."
          className="w-full min-h-[100px] p-3 text-xs rounded-xl bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-700 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none resize-none"
        />

        <div className="flex items-center justify-end space-x-2 mt-3">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 rounded-lg"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={!replyBody.trim() || isSending}
            className="flex items-center space-x-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-xs transition-all"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{isSending ? "Sending..." : "Send Reply"}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
