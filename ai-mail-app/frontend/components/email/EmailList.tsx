/** Paginated Email List Container. */
"use client";

import React from "react";
import { Email } from "@/lib/types";
import { EmailRow } from "./EmailRow";
import { useEmailStore } from "@/stores/emailStore";
import { ChevronLeft, ChevronRight, Inbox, FilterX } from "lucide-react";

interface Props {
  title?: string;
}

export const EmailList: React.FC<Props> = ({ title }) => {
  const {
    emails,
    loading,
    total,
    page,
    totalPages,
    pageSize,
    filters,
    fetchEmails,
    clearFilters,
  } = useEmailStore();

  const hasActiveFilters = Boolean(
    filters.query || filters.sender || filters.daysAgo !== undefined || filters.isRead !== undefined
  );

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden flex flex-col h-full">
      {/* Active Filter Bar if filtered */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between px-4 py-2 bg-blue-50/70 dark:bg-blue-950/30 border-b border-blue-100 dark:border-blue-900/50 text-xs text-blue-700 dark:text-blue-300">
          <div className="flex items-center space-x-2">
            <span>Filtered results ({total} emails found)</span>
            {filters.daysAgo && (
              <span className="bg-blue-100 dark:bg-blue-900/60 px-2 py-0.5 rounded-md text-[10px] font-semibold">
                Last {filters.daysAgo} days
              </span>
            )}
            {filters.query && (
              <span className="bg-blue-100 dark:bg-blue-900/60 px-2 py-0.5 rounded-md text-[10px] font-semibold">
                Query: "{filters.query}"
              </span>
            )}
          </div>
          <button
            onClick={clearFilters}
            className="flex items-center space-x-1 text-xs hover:underline font-medium focus:outline-none"
          >
            <FilterX className="w-3.5 h-3.5" />
            <span>Reset filters</span>
          </button>
        </div>
      )}

      {/* Email Rows List */}
      <div className="flex-1 overflow-y-auto divide-y divide-zinc-100 dark:divide-zinc-800/60">
        {loading && emails.length === 0 ? (
          // Skeleton loading
          <div className="p-6 space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4 animate-pulse">
                <div className="w-4 h-4 bg-zinc-200 dark:bg-zinc-800 rounded-full" />
                <div className="w-32 h-4 bg-zinc-200 dark:bg-zinc-800 rounded-md" />
                <div className="flex-1 h-4 bg-zinc-200 dark:bg-zinc-800 rounded-md" />
                <div className="w-16 h-4 bg-zinc-200 dark:bg-zinc-800 rounded-md" />
              </div>
            ))}
          </div>
        ) : emails.length === 0 ? (
          // Empty State
          <div className="flex flex-col items-center justify-center p-12 text-center h-64">
            <div className="w-12 h-12 rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-400 mb-3">
              <Inbox className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200 mb-1">
              No emails found
            </h3>
            <p className="text-xs text-zinc-500 max-w-sm">
              {hasActiveFilters
                ? "No emails matched your filter criteria. Try clearing filters or searching for something else."
                : "Your folder is currently empty."}
            </p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-4 px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-all"
              >
                Clear all filters
              </button>
            )}
          </div>
        ) : (
          emails.map((email) => <EmailRow key={email.id} email={email} />)
        )}
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-900/60 text-xs text-zinc-500">
        <div>
          Showing {emails.length > 0 ? (page - 1) * pageSize + 1 : 0}–
          {Math.min(page * pageSize, total)} of {total} emails
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => fetchEmails(page - 1)}
            disabled={page <= 1 || loading}
            className="p-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 text-xs font-medium text-zinc-700 dark:text-zinc-300">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => fetchEmails(page + 1)}
            disabled={page >= totalPages || loading}
            className="p-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
