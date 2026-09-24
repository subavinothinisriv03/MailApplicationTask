/** Typed API Client for AI Mail Backend. */
import {
  User,
  Email,
  EmailListResponse,
  ComposePayload,
  AssistantChatRequest,
  AssistantChatResponse,
  ChatMessage
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // send cookies for OAuth session
  });

  if (!res.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Authentication
  async getCurrentUser(): Promise<User> {
    return request<User>("/api/auth/me");
  },

  async demoLogin(): Promise<{ access_token: string; user: User }> {
    const data = await request<{ access_token: string; user: User }>("/api/auth/demo-login", {
      method: "POST",
    });
    if (typeof window !== "undefined" && data.access_token) {
      localStorage.setItem("access_token", data.access_token);
    }
    return data;
  },

  async logout(): Promise<{ message: string }> {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
    return request<{ message: string }>("/api/auth/logout", {
      method: "POST",
    });
  },

  // Emails
  async getEmails(params: {
    folder?: string;
    query?: string;
    sender?: string;
    is_read?: boolean;
    is_starred?: boolean;
    days_ago?: number;
    page?: number;
    page_size?: number;
  }): Promise<EmailListResponse> {
    const sp = new URLSearchParams();
    if (params.folder) sp.set("folder", params.folder);
    if (params.query) sp.set("query", params.query);
    if (params.sender) sp.set("sender", params.sender);
    if (params.is_read !== undefined) sp.set("is_read", String(params.is_read));
    if (params.is_starred !== undefined) sp.set("is_starred", String(params.is_starred));
    if (params.days_ago !== undefined) sp.set("days_ago", String(params.days_ago));
    sp.set("page", String(params.page || 1));
    sp.set("page_size", String(params.page_size || 20));

    return request<EmailListResponse>(`/api/emails?${sp.toString()}`);
  },

  async getInbox(page = 1, pageSize = 20): Promise<EmailListResponse> {
    return this.getEmails({ folder: "inbox", page, page_size: pageSize });
  },

  async getSent(page = 1, pageSize = 20): Promise<EmailListResponse> {
    return this.getEmails({ folder: "sent", page, page_size: pageSize });
  },

  async getEmailById(emailId: string): Promise<Email> {
    return request<Email>(`/api/emails/${emailId}`);
  },

  async sendEmail(payload: ComposePayload): Promise<Email> {
    return request<Email>("/api/emails/send", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async markRead(emailId: string): Promise<Email> {
    return request<Email>(`/api/emails/${emailId}/read`, { method: "POST" });
  },

  async markUnread(emailId: string): Promise<Email> {
    return request<Email>(`/api/emails/${emailId}/unread`, { method: "POST" });
  },

  async starEmail(emailId: string): Promise<Email> {
    return request<Email>(`/api/emails/${emailId}/star`, { method: "POST" });
  },

  async unstarEmail(emailId: string): Promise<Email> {
    return request<Email>(`/api/emails/${emailId}/unstar`, { method: "POST" });
  },

  async replyToEmail(emailId: string, body: string, cc: string[] = [], bcc: string[] = []): Promise<Email> {
    return request<Email>(`/api/emails/${emailId}/reply`, {
      method: "POST",
      body: JSON.stringify({ body, cc, bcc }),
    });
  },

  async deleteEmail(emailId: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/api/emails/${emailId}`, {
      method: "DELETE",
    });
  },

  // Assistant
  async chatWithAssistant(req: AssistantChatRequest): Promise<AssistantChatResponse> {
    return request<AssistantChatResponse>("/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  async getAssistantHistory(): Promise<ChatMessage[]> {
    return request<ChatMessage[]>("/api/assistant/history");
  },

  async clearAssistantHistory(): Promise<{ message: string }> {
    return request<{ message: string }>("/api/assistant/history", {
      method: "DELETE",
    });
  },
};
