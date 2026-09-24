/** Real-time WebSocket Client for AI Mail updates and assistant events. */
import { WebSocketEvent } from "./types";

type EventHandler = (event: WebSocketEvent) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectInterval = 2000;
  private isExplicitlyClosed = false;
  private listeners: Set<EventHandler> = new Set();

  constructor() {
    this.url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
  }

  public connect(): void {
    if (typeof window === "undefined") return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    let socketUrl = this.url;
    const token = localStorage.getItem("access_token");
    if (token) {
      socketUrl += `?token=${encodeURIComponent(token)}`;
    }

    try {
      this.ws = new WebSocket(socketUrl);

      this.ws.onopen = () => {
        console.log("[WebSocket] Connected successfully.");
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (messageEvent) => {
        try {
          const parsed = JSON.parse(messageEvent.data) as WebSocketEvent;
          this.notifyListeners(parsed);
        } catch (e) {
          // Handle string ping/pong
          if (messageEvent.data === "pong") return;
          console.debug("[WebSocket] Received raw message:", messageEvent.data);
        }
      };

      this.ws.onclose = () => {
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (err) => {
        console.warn("[WebSocket] Error occurred:", err);
      };
    } catch (e) {
      console.error("[WebSocket] Exception while connecting:", e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn("[WebSocket] Max reconnect attempts reached.");
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1), 15000);
    console.log(`[WebSocket] Reconnecting in ${Math.round(delay / 1000)}s (attempt ${this.reconnectAttempts})...`);
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public subscribe(handler: EventHandler): () => void {
    this.listeners.add(handler);
    return () => {
      this.listeners.delete(handler);
    };
  }

  private notifyListeners(event: WebSocketEvent): void {
    this.listeners.forEach((handler) => {
      try {
        handler(event);
      } catch (err) {
        console.error("[WebSocket] Listener error:", err);
      }
    });
  }

  public send(data: string | object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const payload = typeof data === "string" ? data : JSON.stringify(data);
      this.ws.send(payload);
    }
  }
}

export const wsClient = new WebSocketClient();
