/** Zustand store for Email data and mailbox state. */
import { create } from "zustand";
import { Email } from "@/lib/types";
import { api } from "@/lib/api";

export interface EmailFilterState {
  query?: string;
  sender?: string;
  isRead?: boolean;
  isStarred?: boolean;
  daysAgo?: number;
}

interface EmailStoreState {
  emails: Email[];
  selectedEmail: Email | null;
  currentFolder: "inbox" | "sent" | "starred";
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  filters: EmailFilterState;
  loading: boolean;
  error: string | null;

  // Actions
  setCurrentFolder: (folder: "inbox" | "sent" | "starred") => void;
  setFilters: (filters: Partial<EmailFilterState>) => void;
  clearFilters: () => void;
  fetchEmails: (page?: number) => Promise<void>;
  selectEmailById: (id: string) => Promise<Email | null>;
  setSelectedEmail: (email: Email | null) => void;
  markAsRead: (emailId: string, isRead?: boolean) => Promise<void>;
  toggleStar: (emailId: string) => Promise<void>;
  deleteEmail: (emailId: string) => Promise<void>;
  addOrUpdateEmail: (email: Email) => void;
}

export const useEmailStore = create<EmailStoreState>((set, get) => ({
  emails: [],
  selectedEmail: null,
  currentFolder: "inbox",
  total: 0,
  page: 1,
  pageSize: 20,
  totalPages: 1,
  filters: {},
  loading: false,
  error: null,

  setCurrentFolder: (folder) => {
    set({ currentFolder: folder, page: 1 });
    get().fetchEmails(1);
  },

  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
      page: 1,
    }));
    get().fetchEmails(1);
  },

  clearFilters: () => {
    set({ filters: {}, page: 1 });
    get().fetchEmails(1);
  },

  fetchEmails: async (pageArg?: number) => {
    const { currentFolder, filters, pageSize } = get();
    const page = pageArg || get().page;
    set({ loading: true, error: null });

    try {
      const data = await api.getEmails({
        folder: currentFolder,
        query: filters.query,
        sender: filters.sender,
        is_read: filters.isRead,
        is_starred: filters.isStarred,
        days_ago: filters.daysAgo,
        page,
        page_size: pageSize,
      });

      set({
        emails: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        totalPages: data.total_pages,
        loading: false,
      });
    } catch (err: any) {
      set({ error: err.message || "Failed to fetch emails.", loading: false });
    }
  },

  selectEmailById: async (id: string) => {
    // Check if already in memory
    const existing = get().emails.find((e) => e.id === id);
    if (existing) {
      set({ selectedEmail: existing });
    }
    try {
      const email = await api.getEmailById(id);
      set((state) => ({
        selectedEmail: email,
        emails: state.emails.map((e) => (e.id === id ? email : e)),
      }));
      return email;
    } catch (err: any) {
      set({ error: err.message || "Failed to load email details." });
      return existing || null;
    }
  },

  setSelectedEmail: (email) => set({ selectedEmail: email }),

  markAsRead: async (emailId: string, isRead = true) => {
    try {
      const updated = isRead ? await api.markRead(emailId) : await api.markUnread(emailId);
      set((state) => ({
        emails: state.emails.map((e) => (e.id === emailId ? updated : e)),
        selectedEmail: state.selectedEmail?.id === emailId ? updated : state.selectedEmail,
      }));
    } catch (err) {
      console.error("Failed to update read status:", err);
    }
  },

  toggleStar: async (emailId: string) => {
    const current = get().emails.find((e) => e.id === emailId) || get().selectedEmail;
    if (!current) return;
    const shouldStar = !current.is_starred;
    try {
      const updated = shouldStar ? await api.starEmail(emailId) : await api.unstarEmail(emailId);
      set((state) => ({
        emails: state.emails.map((e) => (e.id === emailId ? updated : e)),
        selectedEmail: state.selectedEmail?.id === emailId ? updated : state.selectedEmail,
      }));
    } catch (err) {
      console.error("Failed to toggle star:", err);
    }
  },

  deleteEmail: async (emailId: string) => {
    try {
      await api.deleteEmail(emailId);
      set((state) => ({
        emails: state.emails.filter((e) => e.id !== emailId),
        selectedEmail: state.selectedEmail?.id === emailId ? null : state.selectedEmail,
        total: Math.max(0, state.total - 1),
      }));
    } catch (err) {
      console.error("Failed to delete email:", err);
    }
  },

  addOrUpdateEmail: (email: Email) => {
    set((state) => {
      const exists = state.emails.some((e) => e.id === email.id);
      if (exists) {
        return {
          emails: state.emails.map((e) => (e.id === email.id ? email : e)),
          selectedEmail: state.selectedEmail?.id === email.id ? email : state.selectedEmail,
        };
      } else {
        // Prepend new email to list
        return {
          emails: [email, ...state.emails],
          total: state.total + 1,
        };
      }
    });
  },
}));
