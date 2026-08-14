"use client";

import { cn } from "@/lib/utils";

export function SequenceStage({
  step,
  title,
  subtitle,
  mode,
  last = false,
  children,
}: {
  step: number;
  title: string;
  subtitle?: string;
  mode: "sequence" | "parallel";
  last?: boolean;
  children?: React.ReactNode;
}) {
  const parallel = mode === "parallel";

  return (
    <li className="flex gap-3">
      <div className="flex w-9 shrink-0 flex-col items-center">
        <div
          className={cn(
            "flex size-8 items-center justify-center rounded-full border text-xs font-semibold",
            parallel
              ? "border-status-change/40 bg-status-change/15 text-status-change-foreground"
              : "border-primary/30 bg-primary/10 text-primary",
          )}
        >
          {step}
        </div>
        {last ? null : <div className="mt-1 w-px flex-1 min-h-6 bg-border" />}
      </div>
      <div className={cn("min-w-0 flex-1", last ? "pb-1" : "pb-6")}>
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <p className="text-sm font-semibold">{title}</p>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
              parallel
                ? "bg-status-change/15 text-status-change-foreground"
                : "bg-muted text-muted-foreground",
            )}
          >
            {parallel ? "in parallel" : "in sequence"}
          </span>
        </div>
        {subtitle ? (
          <p className="mb-2 text-xs leading-relaxed text-muted-foreground">
            {subtitle}
          </p>
        ) : null}
        {children ? (
          <div
            className={
              parallel
                ? "grid gap-2 sm:grid-cols-2 xl:grid-cols-2"
                : "space-y-2"
            }
          >
            {children}
          </div>
        ) : null}
      </div>
    </li>
  );
}
