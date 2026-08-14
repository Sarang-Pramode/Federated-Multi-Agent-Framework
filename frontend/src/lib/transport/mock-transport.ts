import type { PlatformEvent } from "@/lib/events";

export type MockTransportOptions = {
  intervalMs?: number;
  evalIntervalMs?: number;
  onEvent: (event: PlatformEvent) => void;
  onIdle?: () => void;
};

const EVAL_TYPES = new Set([
  "EVAL_CASE_PASSED",
  "EVAL_CASE_FAILED",
  "AUDITOR_CHECK_PASSED",
  "AUDITOR_CHECK_FAILED",
]);

export class MockTransport {
  private queue: PlatformEvent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private readonly intervalMs: number;
  private readonly evalIntervalMs: number;
  private readonly onEvent: (event: PlatformEvent) => void;
  private readonly onIdle?: () => void;

  constructor(options: MockTransportOptions) {
    this.intervalMs = options.intervalMs ?? 220;
    this.evalIntervalMs = options.evalIntervalMs ?? 70;
    this.onEvent = options.onEvent;
    this.onIdle = options.onIdle;
  }

  get pendingCount(): number {
    return this.queue.length;
  }

  get isBusy(): boolean {
    return this.queue.length > 0 || this.timer !== null;
  }

  play(events: PlatformEvent[]) {
    this.cancelTimer();
    this.queue = [...events];
    this.tick();
  }

  flush() {
    this.cancelTimer();
    const remaining = this.queue;
    this.queue = [];
    for (const event of remaining) {
      this.onEvent(event);
    }
    this.onIdle?.();
  }

  stop() {
    this.cancelTimer();
    this.queue = [];
  }

  private tick = () => {
    const event = this.queue.shift();
    if (!event) {
      this.timer = null;
      this.onIdle?.();
      return;
    }
    this.onEvent(event);
    if (this.queue.length === 0) {
      this.timer = null;
      this.onIdle?.();
      return;
    }
    const delay = EVAL_TYPES.has(this.queue[0].type)
      ? this.evalIntervalMs
      : this.intervalMs;
    this.timer = setTimeout(this.tick, delay);
  };

  private cancelTimer() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}
