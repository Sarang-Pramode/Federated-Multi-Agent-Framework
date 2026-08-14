"use client";

import { cn } from "@/lib/utils";

type ArrowKind = "request" | "delegation" | "audit";

const kindTone: Record<
  ArrowKind,
  { track: string; pulse: string; head: string; label: string }
> = {
  request: {
    track: "bg-primary/25",
    pulse: "bg-primary",
    head: "border-l-primary",
    label: "request",
  },
  delegation: {
    track: "bg-primary/25",
    pulse: "bg-primary",
    head: "border-l-primary",
    label: "delegate",
  },
  audit: {
    track: "bg-status-change/30",
    pulse: "bg-status-change",
    head: "border-l-status-change",
    label: "audit",
  },
};

export function FlowArrow({
  direction,
  kind,
  active,
  visible = true,
  live = false,
}: {
  direction: "right" | "down";
  kind: ArrowKind;
  active: boolean;
  visible?: boolean;
  live?: boolean;
}) {
  const tone = kindTone[kind];

  if (!visible) {
    return <div aria-hidden className="h-full w-full" />;
  }

  if (direction === "down") {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center">
        <div
          className={cn(
            "relative w-[4px] flex-1 overflow-hidden rounded-full",
            tone.track,
            !active && (live ? "opacity-70" : "opacity-35"),
          )}
        >
          {active ? (
            <span
              className={cn(
                "absolute inset-x-0 h-1/2 rounded-full",
                tone.pulse,
                "animate-flow-y",
              )}
            />
          ) : null}
        </div>
        <span
          className={cn(
            "block size-0 border-x-[6px] border-x-transparent border-t-[8px]",
            kind === "audit" ? "border-t-status-change" : "border-t-primary",
            !active && (live ? "opacity-70" : "opacity-35"),
          )}
        />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col items-stretch justify-center gap-0.5 px-0.5">
      {active ? (
        <span className="text-center text-[9px] font-semibold uppercase tracking-wide text-primary">
          {tone.label}
        </span>
      ) : null}
      <div className="flex items-center">
        <div
          className={cn(
            "relative h-[4px] flex-1 overflow-hidden rounded-full",
            tone.track,
            !active && (live ? "opacity-70" : "opacity-35"),
          )}
        >
          {active ? (
            <span
              className={cn(
                "absolute inset-y-0 w-1/2 rounded-full",
                tone.pulse,
                "animate-flow-x",
              )}
            />
          ) : null}
        </div>
        <span
          className={cn(
            "block size-0 border-y-[6px] border-y-transparent border-l-[8px]",
            tone.head,
            !active && (live ? "opacity-70" : "opacity-35"),
          )}
        />
      </div>
    </div>
  );
}
