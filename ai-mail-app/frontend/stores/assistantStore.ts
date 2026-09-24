/** Assistant Zustand store for chat transcript, tool action dispatch, and UI orchestration. */
import { create } from "zustand";
import { ChatMessage, ToolAction } from "@/lib/types";
import { api } from "@/lib/api";
import { useUIStore } from "./uiStore";
import { useEmailStore } from "./emailStore";

interface AssistantStoreState {
  messages: ChatMessage[];
  isTyping: boolean;
  isProcessing: boolean;
  activeToolAction: ToolAction | null;
  toolHistory: ToolAction[];

  // Actions
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  setTyping: (isTyping: boolean) => void;
  setActiveToolAction: (action: ToolAction | null) => void;
  sendMessage: (text: string, router: any, currentView?: string) => Promise<void>;
  dispatchToolAction: (toolAction: ToolAction, router: any) => Promise<void>;
  clearHistory: () => void;
}

export const useAssistantStore = create<AssistantStoreState>((set, get) => ({
  messages: [
    {
      id: "initial_greeting",
      role: "assistant",
      content:
        "Hello! I am your AI Mail Assistant. I don't just answer questions—I actively control your email interface.\n\n" +
        "Try commanding me:\n" +
        "• \"Compose an email to john@example.com with subject Meeting Tomorrow and body Let's meet at 3pm\"\n" +
        "• \"Show emails from the last 10 days\"\n" +
        "• \"Open the latest email from David\"\n" +
        "• \"Reply to this email saying I will attend\"",
      timestamp: new Date().toISOString(),
    },
  ],
  isTyping: false,
  isProcessing: false,
  activeToolAction: null,
  toolHistory: [],

  addMessage: (msg) => {
    const newMessage: ChatMessage = {
      ...msg,
      id: "msg_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6),
      timestamp: new Date().toISOString(),
    };
    set((state) => ({ messages: [...state.messages, newMessage] }));
  },

  setTyping: (isTyping) => set({ isTyping }),

  setActiveToolAction: (action) => set({ activeToolAction: action }),

  clearHistory: async () => {
    try {
      await api.clearAssistantHistory();
    } catch {}
    set({
      messages: [],
      activeToolAction: null,
      toolHistory: [],
    });
  },

  dispatchToolAction: async (toolAction: ToolAction, router: any) => {
    set({
      activeToolAction: toolAction,
      toolHistory: [...get().toolHistory, toolAction],
    });

    const { tool, arguments: args } = toolAction;
    console.log(`[Assistant UI Action] Executing ${tool}:`, args);

    if (tool === "navigate_to_compose") {
      if (router && typeof router.push === "function") {
        router.push("/compose");
      }
    } else if (tool === "fill_compose_form") {
      if (router && typeof router.push === "function") {
        router.push("/compose");
      }
      const uiStore = useUIStore.getState();
      await uiStore.typeDraftAnimated({
        to: Array.isArray(args.to) ? args.to : [args.to || ""],
        cc: Array.isArray(args.cc) ? args.cc : [],
        bcc: Array.isArray(args.bcc) ? args.bcc : [],
        subject: args.subject || "",
        body: args.body || "",
      });
    } else if (tool === "search_emails") {
      const emailStore = useEmailStore.getState();
      emailStore.setFilters({
        query: args.query || undefined,
        daysAgo: args.days_ago || undefined,
      });
      if (router && typeof router.push === "function") {
        router.push("/inbox");
      }
    } else if (tool === "open_email") {
      const emailId = args.email_id;
      if (emailId && router && typeof router.push === "function") {
        router.push(`/email/${emailId}`);
      }
    } else if (tool === "reply_to_email") {
      const emailStore = useEmailStore.getState();
      const uiStore = useUIStore.getState();
      let targetEmail = emailStore.selectedEmail;
      if (!targetEmail && args.email_id) {
        targetEmail = await emailStore.selectEmailById(args.email_id);
      }

      const toRecipient = targetEmail ? [targetEmail.sender] : [];
      let replySubject = targetEmail ? targetEmail.subject : "Reply";
      if (!replySubject.toLowerCase().startsWith("re:")) {
        replySubject = `Re: ${replySubject}`;
      }

      if (router && typeof router.push === "function") {
        router.push("/compose");
      }

      await uiStore.typeDraftAnimated({
        to: toRecipient,
        cc: [],
        bcc: [],
        subject: replySubject,
        body: args.body || "",
      });
    } else if (tool === "send_email") {
      const emailStore = useEmailStore.getState();
      const uiStore = useUIStore.getState();
      uiStore.clearComposeDraft();
      await emailStore.fetchEmails();
      if (router && typeof router.push === "function") {
        router.push("/sent");
      }
    }

    // Keep active tool visual feedback for 1.5s
    setTimeout(() => {
      if (get().activeToolAction?.tool === tool) {
        set({ activeToolAction: null });
      }
    }, 1500);
  },

  sendMessage: async (text: string, router: any, currentView = "inbox") => {
    if (!text.trim() || get().isProcessing) return;

    // 1. Append user message
    get().addMessage({ role: "user", content: text });

    set({ isProcessing: true, isTyping: true });

    // Gather client context
    const emailStore = useEmailStore.getState();
    const uiStore = useUIStore.getState();

    const clientContext = {
      message: text,
      current_view: currentView,
      current_email_id: emailStore.selectedEmail?.id || null,
      current_filters: emailStore.filters,
      draft_state: uiStore.composeDraft,
    };

    try {
      const response = await api.chatWithAssistant(clientContext);

      // 2. Dispatch UI Tool Actions in sequence
      if (response.tool_actions && response.tool_actions.length > 0) {
        for (const action of response.tool_actions) {
          await get().dispatchToolAction(action, router);
        }
      }

      // 3. Append assistant response message
      get().addMessage({
        role: "assistant",
        content: response.message,
        tool_actions: response.tool_actions,
      });
    } catch (err: any) {
      get().addMessage({
        role: "assistant",
        content: `⚠️ Error executing request: ${err.message || "Failed to communicate with AI Assistant."}`,
      });
    } finally {
      set({ isProcessing: false, isTyping: false });
    }
  },
}));
