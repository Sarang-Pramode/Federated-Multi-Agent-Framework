import type { PlatformEvent } from "@/lib/events";

export type TransportHandler = {
  onEvent: (event: PlatformEvent) => void;
  onStatus?: (status: LiveConnectionStatus) => void;
};

export type LiveConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "unavailable";

export type PlatformTransport = {
  start?: () => void;
  stop: () => void;
};
