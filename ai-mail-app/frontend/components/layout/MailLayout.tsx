/** Main Mail Application Layout orchestrating Sidebar, Header, Center View, and Assistant Sidebar. */
"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { AssistantSidebar } from "@/components/assistant/AssistantSidebar";
import { wsClient } from "@/lib/websocket";
import { useEmailStore } from "@/stores/emailStore";
import { useAssistantStore } from "@/stores/assistantStore";
import { WebSocketEvent } from "@/lib/types";

interface Props {
  children: React.ReactNode;
}

export const MailLayout: React.FC<Props> = ({ children }) => {
  const router = useRouter();
  const { addOrUpdateEmail, fetchEmails } = useEmailStore();
  const { setTyping, dispatchToolAction, addMessage } = useAssistantStore();

  useEffect(() => {
    // Initial fetch of mailbox emails
    fetchEmails();

    // Connect WebSocket client
    wsClient.connect();

    // Subscribe to incoming real-time events
    const unsubscribe = wsClient.subscribe((event: WebSocketEvent) => {
      console.log("[WebSocket Event Received]", event);

      if (event.type === "email_sent" && event.data) {
        addOrUpdateEmail(event.data);
      } else if (event.type === "email_updated" && event.data) {
        addOrUpdateEmail(event.data);
      } else if (event.type === "tool_action" && event.tool) {
        dispatchToolAction(
          {
            type: "tool_action",
            tool: event.tool,
            arguments: event.arguments || {},
            result: event.result,
          },
          router
        );
      } else if (event.type === "typing" && event.data) {
        setTyping(Boolean(event.data.is_typing));
      }
    });

    return () => {
      unsubscribe();
    };
  }, [addOrUpdateEmail, dispatchToolAction, fetchEmails, router, setTyping]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-zinc-100 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 antialiased selection:bg-blue-500 selection:text-white">
      {/* Left Navigation Sidebar */}
      <Sidebar />

      {/* Center Main Stage */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-zinc-50 dark:bg-zinc-900/60 p-4 sm:p-6">
          {children}
        </main>
      </div>

      {/* Right AI Assistant Sidebar */}
      <AssistantSidebar />
    </div>
  );
};
