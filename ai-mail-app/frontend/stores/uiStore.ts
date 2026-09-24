/** UI State management store for theme, assistant panel, and compose state. */
import { create } from "zustand";

export interface ComposeDraft {
  to: string[];
  cc: string[];
  bcc: string[];
  subject: string;
  body: string;
}

interface UIStoreState {
  isAssistantOpen: boolean;
  theme: "light" | "dark" | "system";
  composeDraft: ComposeDraft;
  isTypingAnimationActive: boolean;
  activelyTypingField: string | null;

  // Actions
  toggleAssistant: () => void;
  setAssistantOpen: (open: boolean) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setComposeDraft: (draft: Partial<ComposeDraft>) => void;
  updateDraftField: (field: keyof ComposeDraft, value: any) => void;
  clearComposeDraft: () => void;
  setTypingAnimationState: (isActive: boolean, field?: string | null) => void;
  typeDraftAnimated: (
    targetDraft: ComposeDraft,
    onStep?: (field: string, partialValue: string) => void,
    onComplete?: () => void
  ) => Promise<void>;
}

export const useUIStore = create<UIStoreState>((set, get) => ({
  isAssistantOpen: true,
  theme: "dark",
  composeDraft: {
    to: [],
    cc: [],
    bcc: [],
    subject: "",
    body: "",
  },
  isTypingAnimationActive: false,
  activelyTypingField: null,

  toggleAssistant: () => set((state) => ({ isAssistantOpen: !state.isAssistantOpen })),
  setAssistantOpen: (open) => set({ isAssistantOpen: open }),

  setTheme: (theme) => {
    set({ theme });
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", theme);
      const isDark =
        theme === "dark" ||
        (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
      if (isDark) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }
  },

  setComposeDraft: (draft) =>
    set((state) => ({ composeDraft: { ...state.composeDraft, ...draft } })),

  updateDraftField: (field, value) =>
    set((state) => ({
      composeDraft: { ...state.composeDraft, [field]: value },
    })),

  clearComposeDraft: () =>
    set({
      composeDraft: { to: [], cc: [], bcc: [], subject: "", body: "" },
      isTypingAnimationActive: false,
      activelyTypingField: null,
    }),

  setTypingAnimationState: (isActive, field = null) =>
    set({ isTypingAnimationActive: isActive, activelyTypingField: field }),

  typeDraftAnimated: async (targetDraft, onStep, onComplete) => {
    set({
      isTypingAnimationActive: true,
      composeDraft: { to: [], cc: [], bcc: [], subject: "", body: "" },
    });

    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

    // 1. Animate TO field
    const toText = (targetDraft.to || []).join(", ");
    if (toText) {
      set({ activelyTypingField: "to" });
      let currentTo = "";
      for (const char of toText) {
        currentTo += char;
        set((state) => ({
          composeDraft: { ...state.composeDraft, to: [currentTo] },
        }));
        if (onStep) onStep("to", currentTo);
        await sleep(25);
      }
      // Finalize parsed array
      set((state) => ({
        composeDraft: { ...state.composeDraft, to: targetDraft.to },
      }));
      await sleep(150);
    }

    // 2. Animate SUBJECT field
    const subjectText = targetDraft.subject || "";
    if (subjectText) {
      set({ activelyTypingField: "subject" });
      let currentSubj = "";
      for (const char of subjectText) {
        currentSubj += char;
        set((state) => ({
          composeDraft: { ...state.composeDraft, subject: currentSubj },
        }));
        if (onStep) onStep("subject", currentSubj);
        await sleep(20);
      }
      await sleep(150);
    }

    // 3. Animate BODY field
    const bodyText = targetDraft.body || "";
    if (bodyText) {
      set({ activelyTypingField: "body" });
      let currentBody = "";
      // For longer bodies, type in small chunks of 2-3 characters for realism & speed
      for (let i = 0; i < bodyText.length; i += 2) {
        currentBody += bodyText.slice(i, i + 2);
        set((state) => ({
          composeDraft: { ...state.composeDraft, body: currentBody },
        }));
        if (onStep) onStep("body", currentBody);
        await sleep(15);
      }
      set((state) => ({
        composeDraft: { ...state.composeDraft, body: bodyText },
      }));
      await sleep(150);
    }

    set({ isTypingAnimationActive: false, activelyTypingField: null });
    if (onComplete) onComplete();
  },
}));
