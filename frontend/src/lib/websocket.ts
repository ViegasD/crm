// WebSocket client wrapper — handles connection, reconnection, and typed event dispatch

export type WsEventType = "message.new" | "conversation.updated" | "pong";

export interface WsEvent {
  type: WsEventType;
  [key: string]: unknown;
}

type Listener = (event: WsEvent) => void;

export class WorkspaceSocket {
  private ws: WebSocket | null = null;
  private workspaceId: string;
  private token: string;
  private listeners: Set<Listener> = new Set();
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;
  private backoff = 1000;

  constructor(workspaceId: string, token: string) {
    this.workspaceId = workspaceId;
    this.token = token;
  }

  connect(): void {
    const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
      .replace(/^http/, "ws");
    const url = `${base}/ws/${this.workspaceId}?token=${encodeURIComponent(this.token)}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.backoff = 1000;
      // Start heartbeat ping every 25s
      this._startPing();
    };

    this.ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as WsEvent;
        this.listeners.forEach((l) => l(data));
      } catch {
        // plain "pong" string
      }
    };

    this.ws.onclose = () => {
      this._stopPing();
      if (!this.intentionalClose) {
        this.reconnectTimeout = setTimeout(() => {
          this.backoff = Math.min(this.backoff * 2, 30000);
          this.connect();
        }, this.backoff);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    this._stopPing();
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    this.ws?.close();
  }

  on(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private _pingInterval: ReturnType<typeof setInterval> | null = null;

  private _startPing(): void {
    this._pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 25000);
  }

  private _stopPing(): void {
    if (this._pingInterval) {
      clearInterval(this._pingInterval);
      this._pingInterval = null;
    }
  }
}
