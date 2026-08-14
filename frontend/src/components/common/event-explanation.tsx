"use client";

import { explainEvent } from "@/lib/explain";
import type { PlatformEvent } from "@/lib/events";

export function EventExplanation({ event }: { event: PlatformEvent }) {
  const { technical, explanation } = explainEvent(event);
  return (
    <div className="space-y-1.5 text-sm">
      <p className="font-mono text-[11px] leading-relaxed text-muted-foreground">
        {technical}
      </p>
      <p className="leading-relaxed text-foreground">{explanation}</p>
    </div>
  );
}
