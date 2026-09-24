/** Detailed Email View component. */
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Email } from "@/lib/types";
import { useEmailStore } from "@/stores/emailStore";
import { ReplyForm } from "./ReplyForm";
import {
  ArrowLeft,
  Star,
  Trash2,
  Mail,
  MailOpen,
  Reply,
  Calendar,
  User,
  ExternalLink,
} from "lucide-react";

interface Props {
  email: Email;
}

export const EmailDetail: React.FC<Props> = ({ email }) => {
  const router = useRouter();
  const { toggleStar, markAsRead, deleteEmail } = useEmailStore();
  const [showReplyForm, setShowReplyForm] = useState(false);

  const handleDelete = async () => {
    if (confirm("Move this email to trash?")) {
      await deleteEmail(email.id);
      router.push("/inbox");
    }
  };

  const handleToggleStar = () => {
    toggleStar(email.id);
  };

  const handleToggleRead = () => {
    markAsRead(email.id, !email.is_read);
  };

  const formatFullDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleString([], {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="max-w-4xl mx-auto bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden flex flex-col min-h-[calc(100vh-140px)]">
      {/* Top Action Toolbar */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50">
        <button
          onClick={() => router.back()}
          className="flex items-center space-x-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 p-1.5 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        <div className="flex items-center space-x-1">
          <button
            onClick={handleToggleStar}
            className="p-2 text-zinc-400 hover:text-amber-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title={email.is_starred ? "Unstar" : "Star"}
          >
            <Star
              className={`w-4 h-4 ${
                email.is_starred ? "text-amber-400 fill-amber-400" : ""
              }`}
            />
          </button>

          <button
            onClick={handleToggleRead}
            className="p-2 text-zinc-400 hover:text-blue-500 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title={email.is_read ? "Mark as unread" : "Mark as read"}
          >
            {email.is_read ? <Mail className="w-4 h-4" /> : <MailOpen className="w-4 h-4 text-blue-500" />}
          </button>

          <button
            onClick={() => setShowReplyForm(!showReplyForm)}
            className="p-2 text-zinc-400 hover:text-indigo-500 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="Reply"
          >
            <Reply className="w-4 h-4" />
          </button>

          <button
            onClick={handleDelete}
            className="p-2 text-zinc-400 hover:text-rose-500 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="Delete Email"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 md:p-8 overflow-y-auto">
        {/* Subject Header */}
        <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-6 leading-tight">
          {email.subject || "(No Subject)"}
        </h1>

        {/* Sender & Recipient Card */}
        <div className="flex items-start justify-between pb-6 border-b border-zinc-100 dark:border-zinc-800/80 mb-6">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-sm">
              {(email.sender_name || email.sender || "U")[0].toUpperCase()}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  {email.sender_name || email.sender}
                </span>
                <span className="text-xs text-zinc-400 dark:text-zinc-500">
                  &lt;{email.sender}&gt;
                </span>
              </div>
              <div className="text-xs text-zinc-500 mt-0.5">
                to {email.recipients.join(", ") || "me"}
              </div>
            </div>
          </div>

          <div className="text-xs text-zinc-400 dark:text-zinc-500 flex items-center space-x-1">
            <Calendar className="w-3.5 h-3.5" />
            <span>{formatFullDate(email.received_at)}</span>
          </div>
        </div>

        {/* Email Body */}
        <div className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200 whitespace-pre-wrap font-sans min-h-[160px]">
          {email.body}
        </div>

        {/* Inline Reply Form Toggle / Component */}
        {showReplyForm ? (
          <ReplyForm email={email} onClose={() => setShowReplyForm(false)} />
        ) : (
          <div className="mt-8 pt-6 border-t border-zinc-100 dark:border-zinc-800/80">
            <button
              onClick={() => setShowReplyForm(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 text-xs font-semibold rounded-xl transition-colors shadow-xs"
            >
              <Reply className="w-4 h-4" />
              <span>Reply to {email.sender_name || email.sender}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
