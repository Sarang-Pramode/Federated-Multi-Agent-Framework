import type { PlatformEvent } from "@/lib/events";
import type { LiveConnectionStatus, PlatformTransport } from "@/lib/transport/types";

export type LiveTransportOptions = {
  url?: string;
  onEvent: (event: PlatformEvent) => void;
  onStatus: (status: LiveConnectionStatus) => void;
};

function isPlatformEvent(value: unknown): value is PlatformEvent {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    "id" in value &&
    "ts" in value
  );
}

export class LiveTransport implements PlatformTransport {
  private source: EventSource | null = null;
  private readonly url: string;
  private readonly onEvent: (event: PlatformEvent) => void;
  private readonly onStatus: (status: LiveConnectionStatus) => void;

  constructor(options: LiveTransportOptions) {
    this.url =
      options.url ??
      `${process.env.NEXT_PUBLIC_CENTRAL_URL ?? "http://localhost:8000"}/events`;
    this.onEvent = options.onEvent;
    this.onStatus = options.onStatus;
  }

  start() {
    this.stop();
    this.onStatus("connecting");

    if (typeof window === "undefined" || typeof EventSource === "undefined") {
      this.onStatus("unavailable");
      return;
    }

    try {
      this.source = new EventSource(this.url);
    } catch {
      this.onStatus("unavailable");
      return;
    }

    const timeout = window.setTimeout(() => {
      if (!this.source || this.source.readyState !== EventSource.OPEN) {
        this.stop();
        this.onStatus("unavailable");
      }
    }, 1800);

    this.source.onopen = () => {
      window.clearTimeout(timeout);
      this.onStatus("connected");
    };

    this.source.onerror = () => {
      window.clearTimeout(timeout);
      this.stop();
      this.onStatus("unavailable");
    };

    this.source.onmessage = (message) => {
      try {
        const parsed: unknown = JSON.parse(message.data);
        if (isPlatformEvent(parsed)) {
          this.onEvent(parsed);
        }
      } catch {
        // Ignore malformed frames; live mode is best-effort in Phase 1.
      }
    };
  }

  stop() {
    this.source?.close();
    this.source = null;
  }
}
