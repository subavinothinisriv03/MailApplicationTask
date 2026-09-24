/** Persistent AI Assistant Sidebar controlling the Mail UI. */
"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAssistantStore } from "@/stores/assistantStore";
import { useUIStore } from "@/stores/uiStore";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";
import { ToolActionIndicator } from "./ToolActionIndicator";
import {
  Bot,
  Send,
  Trash2,
  X,
  Sparkles,
  ChevronRight,
  Command,
  Zap,
} from "lucide-react";

export const AssistantSidebar: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isTyping,
    isProcessing,
    activeToolAction,
    sendMessage,
    clearHistory,
  } = useAssistantStore();

  const { isAssistantOpen, setAssistantOpen } = useUIStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, activeToolAction]);

  const handleSend = async (textToSend?: string) => {
    const msg = textToSend || inputMessage;
    if (!msg.trim() || isProcessing) return;
    setInputMessage("");

    // Detect current view from pathname
    let view = "inbox";
    if (pathname.includes("/sent")) view = "sent";
    else if (pathname.includes("/compose")) view = "compose";
    else if (pathname.includes("/email/")) view = "email_detail";

    await sendMessage(msg, router, view);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestionChips = [
    {
      label: "Compose to John",
      command: "Compose an email to john@example.com with subject Meeting Tomorrow and body Let's meet at 3pm",
    },
    {
      label: "Show last 10 days",
      command: "Show emails from the last 10 days",
    },
    {
      label: "Open latest from David",
      command: "Open the latest email from David",
    },
    {
      label: "Reply to this",
      command: "Reply to this email saying I will attend tomorrow's meeting",
    },
    {
      label: "Send email",
      command: "Send the email",
    },
  ];

  if (!isAssistantOpen) {
    return (
      <button
        onClick={() => setAssistantOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center space-x-2.5 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium text-xs rounded-full shadow-xl hover:shadow-blue-500/25 hover:scale-105 transition-all duration-200"
        title="Open AI Assistant"
      >
        <Sparkles className="w-4 h-4 animate-spin [animation-duration:4s]" />
        <span>Ask AI Assistant</span>
      </button>
    );
  }

  return (
    <aside className="w-80 md:w-96 flex flex-col h-full bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 shadow-xl transition-all duration-300 z-30">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/70 backdrop-blur-md">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-blue-600/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center border border-blue-500/20">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <h2 className="text-xs font-bold text-zinc-900 dark:text-zinc-100">AI Mail Controller</h2>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <p className="text-[10px] text-zinc-500 dark:text-zinc-400">Actively controls the interface</p>
          </div>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={clearHistory}
            className="p-1.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setAssistantOpen(false)}
            className="p-1.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            title="Close Sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Live Action Banner */}
      {activeToolAction && (
        <div className="px-4 py-2 bg-blue-50 dark:bg-blue-950/40 border-b border-blue-200/60 dark:border-blue-900/60 animate-in fade-in duration-200">
          <div className="text-[10px] uppercase font-semibold tracking-wider text-blue-600 dark:text-blue-400 mb-1 flex items-center space-x-1">
            <Zap className="w-3 h-3 animate-pulse text-blue-500" />
            <span>Active UI Command</span>
          </div>
          <ToolActionIndicator action={activeToolAction} />
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isTyping && (
          <div className="flex justify-start mb-2">
            <TypingIndicator />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      <div className="px-3 py-2 border-t border-zinc-100 dark:border-zinc-800/60 bg-zinc-50/50 dark:bg-zinc-900/30 overflow-x-auto no-scrollbar">
        <div className="flex space-x-1.5">
          {suggestionChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip.command)}
              disabled={isProcessing}
              className="flex-shrink-0 text-[10px] font-medium px-2.5 py-1 rounded-full bg-zinc-200/60 dark:bg-zinc-800 hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-900/30 dark:hover:text-blue-400 text-zinc-600 dark:text-zinc-300 border border-zinc-200/40 dark:border-zinc-700/60 transition-colors"
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Command AI (e.g. 'Compose to David...')"
            disabled={isProcessing}
            className="w-full text-xs py-2.5 pl-3 pr-10 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 border border-transparent focus:border-blue-500 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-zinc-900 focus:outline-none transition-all"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputMessage.trim() || isProcessing}
            className="absolute right-1.5 p-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 text-white rounded-lg transition-colors shadow-sm"
            title="Send Instruction"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="mt-1.5 text-[10px] text-zinc-400 dark:text-zinc-500 flex items-center space-x-1 justify-center">
          <Command className="w-2.5 h-2.5" />
          <span>Natural language commands directly control the app</span>
        </p>
      </div>
    </aside>
  );
};
