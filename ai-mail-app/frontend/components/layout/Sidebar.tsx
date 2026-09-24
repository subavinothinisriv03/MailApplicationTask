/** Left Navigation Sidebar for AI Mail App. */
"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEmailStore } from "@/stores/emailStore";
import { useUIStore } from "@/stores/uiStore";
import {
  Inbox,
  Send,
  Star,
  PlusCircle,
  Moon,
  Sun,
  Laptop,
  Mail,
  LogOut,
  Sparkles
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { currentFolder, emails, setCurrentFolder } = useEmailStore();
  const { theme, setTheme, toggleAssistant, isAssistantOpen } = useUIStore();

  const unreadCount = emails.filter((e) => !e.is_read && !e.is_sent).length;

  const navItems = [
    {
      id: "inbox",
      label: "Inbox",
      href: "/inbox",
      icon: Inbox,
      badge: unreadCount > 0 ? unreadCount : null,
    },
    {
      id: "sent",
      label: "Sent",
      href: "/sent",
      icon: Send,
      badge: null,
    },
  ];

  return (
    <aside className="w-60 flex flex-col h-full bg-zinc-50 dark:bg-zinc-900/90 border-r border-zinc-200 dark:border-zinc-800 select-none">
      {/* Brand Header */}
      <div className="flex items-center space-x-2.5 px-5 py-4 border-b border-zinc-200/60 dark:border-zinc-800">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
          <Mail className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 tracking-tight">
            AI Mail
          </h1>
          <p className="text-[10px] text-zinc-400 font-medium">Autonomous UI Control</p>
        </div>
      </div>

      {/* Compose Action Button */}
      <div className="p-4">
        <Link
          href="/compose"
          className="flex items-center justify-center space-x-2 w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-medium text-xs rounded-xl shadow-md shadow-blue-500/20 hover:shadow-blue-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Message</span>
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={() => setCurrentFolder(item.id as any)}
              className={`flex items-center justify-between px-3 py-2 text-xs font-medium rounded-xl transition-all ${
                isActive
                  ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-200/60 dark:border-blue-900/60 shadow-xs"
                  : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/60 hover:text-zinc-900 dark:hover:text-zinc-200"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Icon className={`w-4 h-4 ${isActive ? "text-blue-600 dark:text-blue-400" : "text-zinc-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== null && (
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* AI Assistant Quick Toggle */}
      <div className="px-3 py-2 border-t border-zinc-200/60 dark:border-zinc-800">
        <button
          onClick={toggleAssistant}
          className={`flex items-center justify-between w-full px-3 py-2 text-xs rounded-xl font-medium transition-all ${
            isAssistantOpen
              ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-900/60"
              : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/60"
          }`}
        >
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-indigo-500" />
            <span>AI Assistant</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-zinc-200/60 dark:bg-zinc-800 text-zinc-500">
            {isAssistantOpen ? "Open" : "Hidden"}
          </span>
        </button>
      </div>

      {/* Theme & User Preferences */}
      <div className="p-3 border-t border-zinc-200 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50 flex items-center justify-between">
        <div className="flex items-center space-x-1 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl">
          <button
            onClick={() => setTheme("light")}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === "light"
                ? "bg-white text-amber-500 shadow-xs"
                : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            }`}
            title="Light Mode"
          >
            <Sun className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setTheme("dark")}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === "dark"
                ? "bg-zinc-700 text-blue-400 shadow-xs"
                : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            }`}
            title="Dark Mode"
          >
            <Moon className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setTheme("system")}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === "system"
                ? "bg-white dark:bg-zinc-700 text-zinc-800 dark:text-zinc-200 shadow-xs"
                : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            }`}
            title="System Mode"
          >
            <Laptop className="w-3.5 h-3.5" />
          </button>
        </div>

        <Link
          href="/api/auth/logout"
          onClick={(e) => {
            e.preventDefault();
            if (typeof window !== "undefined") {
              localStorage.removeItem("access_token");
              window.location.href = "/";
            }
          }}
          className="p-2 text-zinc-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20 rounded-xl transition-colors"
          title="Sign Out"
        >
          <LogOut className="w-3.5 h-3.5" />
        </Link>
      </div>
    </aside>
  );
};
