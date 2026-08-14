"use client";

import { cn } from "@/lib/utils";
import {
  domainStatusLabel,
  domainStatusTone,
  StatusBadge,
} from "@/components/common/status-badge";
import type { DomainState } from "@/lib/types";

export function NodeCard({
  title,
  subtitle,
  status,
  isolateHealthy,
  dimmed,
  active,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  status?: DomainState["status"] | "active";
  isolateHealthy?: boolean;
  dimmed?: boolean;
  active?: boolean;
  children?: React.ReactNode;
  className?: string;
}) {
  const tone =
    status === "active" || status === "healthy"
      ? domainStatusTone(status)
      : status
        ? domainStatusTone(status)
        : "neutral";

  return (
    <div
      className={cn(
        "min-w-0 rounded-xl border bg-card px-3 py-2.5 shadow-sm transition-all",
        dimmed && "opacity-45 grayscale",
        active && "border-primary ring-2 ring-primary/20",
        !active && "border-border",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-foreground">{title}</p>
          {subtitle ? (
            <p className="truncate font-mono text-[11px] text-muted-foreground">
              {subtitle}
            </p>
          ) : null}
        </div>
        {status ? (
          <StatusBadge tone={tone}>
            {status === "active" && !isolateHealthy
              ? "Active"
              : domainStatusLabel(status, isolateHealthy)}
          </StatusBadge>
        ) : null}
      </div>
      {children}
    </div>
  );
}
