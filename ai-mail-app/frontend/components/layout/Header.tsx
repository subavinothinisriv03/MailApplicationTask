/** Top Application Header with live search, filters, and sync status. */
"use client";

import React, { useState, useEffect } from "react";
import { useEmailStore } from "@/stores/emailStore";
import { useUIStore } from "@/stores/uiStore";
import { Search, RotateCw, Calendar, Sparkles, SlidersHorizontal, Check } from "lucide-react";

export const Header: React.FC = () => {
  const { filters, setFilters, clearFilters, fetchEmails, loading } = useEmailStore();
  const { toggleAssistant, isAssistantOpen } = useUIStore();
  const [searchValue, setSearchValue] = useState(filters.query || "");

  useEffect(() => {
    setSearchValue(filters.query || "");
  }, [filters.query]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters({ query: searchValue.trim() || undefined });
  };

  const handleDateFilter = (days?: number) => {
    setFilters({ daysAgo: days });
  };

  const handleReadFilter = (isRead?: boolean) => {
    setFilters({ isRead });
  };

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md z-10">
      {/* Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="flex-1 max-w-lg relative">
        <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400" />
        <input
          type="text"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Search emails by sender, subject, keyword..."
          className="w-full text-xs py-2 pl-9 pr-8 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 border border-transparent focus:border-blue-500 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-zinc-950 focus:outline-none transition-all shadow-xs"
        />
        {searchValue && (
          <button
            type="button"
            onClick={() => {
              setSearchValue("");
              clearFilters();
            }}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
          >
            ×
          </button>
        )}
      </form>

      {/* Filter Chips & Action Controls */}
      <div className="flex items-center space-x-2.5 ml-4">
        {/* Quick Date Range Filters */}
        <div className="hidden sm:flex items-center space-x-1 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl text-[11px]">
          <button
            onClick={() => handleDateFilter(undefined)}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filters.daysAgo === undefined
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            All
          </button>
          <button
            onClick={() => handleDateFilter(10)}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filters.daysAgo === 10
                ? "bg-blue-600 text-white shadow-xs"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            Last 10 Days
          </button>
          <button
            onClick={() => handleDateFilter(30)}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filters.daysAgo === 30
                ? "bg-blue-600 text-white shadow-xs"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            Last 30 Days
          </button>
        </div>

        {/* Read / Unread Filter */}
        <div className="hidden md:flex items-center space-x-1 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl text-[11px]">
          <button
            onClick={() => handleReadFilter(undefined)}
            className={`px-2 py-1 rounded-lg font-medium transition-colors ${
              filters.isRead === undefined
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            Any
          </button>
          <button
            onClick={() => handleReadFilter(false)}
            className={`px-2 py-1 rounded-lg font-medium transition-colors ${
              filters.isRead === false
                ? "bg-blue-600 text-white shadow-xs"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            Unread
          </button>
        </div>

        {/* Refresh Button */}
        <button
          onClick={() => fetchEmails()}
          disabled={loading}
          className="p-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200/70 dark:hover:bg-zinc-700 rounded-xl transition-all"
          title="Refresh Mailbox"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-blue-500" : ""}`} />
        </button>

        {/* Assistant Toggle Button */}
        <button
          onClick={toggleAssistant}
          className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-xl border transition-all ${
            isAssistantOpen
              ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-900"
              : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-transparent hover:border-zinc-300 dark:hover:border-zinc-700"
          }`}
          title="Toggle Assistant Sidebar"
        >
          <Sparkles className="w-3.5 h-3.5 text-blue-500" />
          <span className="hidden sm:inline">AI Controller</span>
        </button>
      </div>
    </header>
  );
};
