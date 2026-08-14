"use client";

import { cn } from "@/lib/utils";
import type { DomainStatus, EvalVerdict, ReleaseStatus } from "@/lib/types";

type Tone = "healthy" | "change" | "fail" | "offline" | "neutral";

const toneClass: Record<Tone, string> = {
  healthy:
    "border-status-healthy/30 bg-status-healthy/10 text-status-healthy-foreground",
  change:
    "border-status-change/40 bg-status-change/15 text-status-change-foreground",
  fail: "border-status-fail/30 bg-status-fail/10 text-status-fail-foreground",
  offline: "border-border bg-muted text-muted-foreground",
  neutral: "border-primary/20 bg-primary/10 text-primary",
};

export function StatusBadge({
  children,
  tone,
  className,
}: {
  children: React.ReactNode;
  tone: Tone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded-full border px-2 text-[11px] font-medium tracking-wide uppercase",
        toneClass[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function domainStatusTone(status: DomainStatus): Tone {
  if (status === "active" || status === "healthy") return "healthy";
  if (status === "unavailable") return "fail";
  return "offline";
}

export function domainStatusLabel(
  status: DomainStatus,
  isolateHealthy?: boolean,
): string {
  if (status === "unavailable") return "Unavailable";
  if (status === "offline") return "Offline";
  if (isolateHealthy) return "Healthy";
  return "Active";
}

export function evalTone(verdict?: EvalVerdict | "pass" | "fail" | "pending" | "none"): Tone {
  if (verdict === "PASS" || verdict === "pass") return "healthy";
  if (verdict === "REGRESSION_DETECTED" || verdict === "fail") return "fail";
  if (verdict === "RUNNING" || verdict === "pending") return "change";
  return "offline";
}

export function releaseTone(status: ReleaseStatus): Tone {
  if (status === "REGRESSION_DETECTED") return "fail";
  if (status === "passing") return "healthy";
  return "neutral";
}
