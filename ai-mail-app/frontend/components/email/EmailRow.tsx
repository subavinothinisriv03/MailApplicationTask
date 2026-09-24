/** Single Email Row in the mailbox list. */
"use client";

import React from "react";
import Link from "next/link";
import { Email } from "@/lib/types";
import { useEmailStore } from "@/stores/emailStore";
import { Star, Mail, CheckCircle2 } from "lucide-react";

interface Props {
  email: Email;
}

export const EmailRow: React.FC<Props> = ({ email }) => {
  const { toggleStar, markAsRead } = useEmailStore();

  const handleStarClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleStar(email.id);
  };

  const handleToggleRead = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    markAsRead(email.id, !email.is_read);
  };

  // Format date cleanly
  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      const now = new Date();
      const isToday = d.toDateString() === now.toDateString();
      if (isToday) {
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      }
      return d.toLocaleDateString([], { month: "short", day: "numeric" });
    } catch {
      return "";
    }
  };

  return (
    <Link
      href={`/email/${email.id}`}
      className={`group flex items-center px-4 py-3 border-b border-zinc-200/70 dark:border-zinc-800/80 hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60 transition-all cursor-pointer select-none ${
        !email.is_read
          ? "bg-white dark:bg-zinc-900/90 font-semibold"
          : "bg-zinc-50/50 dark:bg-zinc-900/30 font-normal text-zinc-600 dark:text-zinc-400"
      }`}
    >
      {/* Unread dot and Star */}
      <div className="flex items-center space-x-3 mr-3 flex-shrink-0">
        <button
          onClick={handleToggleRead}
          title={email.is_read ? "Mark as unread" : "Mark as read"}
          className="focus:outline-none"
        >
          <div
            className={`w-2 h-2 rounded-full transition-all ${
              !email.is_read ? "bg-blue-600 shadow-sm shadow-blue-500/50" : "bg-transparent hover:bg-zinc-300"
            }`}
          />
        </button>

        <button
          onClick={handleStarClick}
          className="text-zinc-300 dark:text-zinc-600 hover:text-amber-400 transition-colors focus:outline-none"
          title={email.is_starred ? "Unstar" : "Star"}
        >
          <Star
            className={`w-4 h-4 ${
              email.is_starred ? "text-amber-400 fill-amber-400" : "hover:scale-110"
            } transition-transform`}
          />
        </button>
      </div>

      {/* Sender info */}
      <div className="w-36 sm:w-48 flex-shrink-0 truncate pr-3 text-xs text-zinc-900 dark:text-zinc-200">
        {email.sender_name || email.sender}
      </div>

      {/* Subject and Snippet */}
      <div className="flex-1 flex items-center min-w-0 pr-4 text-xs truncate">
        <span className="text-zinc-900 dark:text-zinc-100 mr-2 truncate">
          {email.subject || "(No Subject)"}
        </span>
        <span className="text-zinc-400 dark:text-zinc-500 truncate hidden sm:inline">
          — {email.snippet || email.body.slice(0, 100)}
        </span>
      </div>

      {/* Timestamp */}
      <div className="flex-shrink-0 text-[11px] text-zinc-400 dark:text-zinc-500 text-right">
        {formatDate(email.received_at)}
      </div>
    </Link>
  );
};
