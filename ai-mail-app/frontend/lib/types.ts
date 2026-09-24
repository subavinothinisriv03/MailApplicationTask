/** Type definitions for AI Mail Application. */

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Email {
  id: string;
  user_id: string;
  gmail_id?: string | null;
  thread_id?: string | null;
  sender: string;
  sender_name?: string | null;
  recipients: string[];
  cc: string[];
  bcc: string[];
  subject: string;
  body: string;
  snippet?: string | null;
  is_read: boolean;
  is_starred: boolean;
  is_sent: boolean;
  labels: string[];
  received_at: string;
  created_at: string;
  updated_at: string;
}

export interface EmailListResponse {
  items: Email[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ComposePayload {
  to: string[];
  cc?: string[];
  bcc?: string[];
  subject: string;
  body: string;
  thread_id?: string;
  reply_to_id?: string;
}

export interface ToolAction {
  type: string;
  tool: "navigate_to_compose" | "fill_compose_form" | "search_emails" | "open_email" | "reply_to_email" | "send_email" | string;
  arguments: Record<string, any>;
  result?: any;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  tool_actions?: ToolAction[];
  timestamp: string;
}

export interface AssistantChatRequest {
  message: string;
  current_view?: "inbox" | "sent" | "compose" | "email_detail" | string;
  current_email_id?: string | null;
  current_filters?: Record<string, any> | null;
  draft_state?: {
    to?: string[];
    cc?: string[];
    bcc?: string[];
    subject?: string;
    body?: string;
  } | null;
}

export interface AssistantChatResponse {
  message: string;
  tool_actions: ToolAction[];
  execution_context?: Record<string, any>;
}

export interface WebSocketEvent {
  type: "email_sent" | "email_updated" | "assistant_action" | "tool_action" | "typing" | "connection_established";
  data?: any;
  tool?: string;
  arguments?: Record<string, any>;
  result?: any;
  user_id?: string;
  message?: string;
}
