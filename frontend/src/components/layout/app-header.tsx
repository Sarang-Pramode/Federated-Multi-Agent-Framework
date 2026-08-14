"use client";

import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  releaseTone,
  StatusBadge,
} from "@/components/common/status-badge";
import { usePlatform } from "@/providers/platform-provider";
import { cn } from "@/lib/utils";

export function AppHeader() {
  const {
    mode,
    setMode,
    stepIndex,
    stepCount,
    currentStep,
    reset,
    state,
    liveStatus,
  } = usePlatform();

  return (
    <header className="flex shrink-0 items-center justify-between gap-4 border-b border-border bg-card px-5 py-3">
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Federated Agent Platform
        </p>
        <h1 className="truncate text-lg font-semibold tracking-tight text-foreground">
          Architecture Demo
        </h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex rounded-lg border border-border bg-muted/60 p-0.5">
          <button
            type="button"
            onClick={() => setMode("demo")}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-medium transition-colors",
              mode === "demo"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Demo Mode
          </button>
          <button
            type="button"
            onClick={() => setMode("live")}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-medium transition-colors",
              mode === "live"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Live Mode
          </button>
        </div>

        <div className="hidden items-center gap-2 sm:flex">
          <span className="text-xs text-muted-foreground">
            Step {stepIndex + 1} of {stepCount}
          </span>
          <span className="max-w-56 truncate text-sm font-medium text-foreground">
            {currentStep.title}
          </span>
        </div>

        <StatusBadge tone={releaseTone(state.releaseStatus)}>
          {state.releaseStatus === "REGRESSION_DETECTED"
            ? "Regression"
            : state.releaseStatus === "passing"
              ? "Passing"
              : "Stable"}
        </StatusBadge>

        {liveStatus === "connecting" ? (
          <span className="text-xs text-status-change-foreground">Connecting…</span>
        ) : null}

        <Button variant="outline" size="sm" onClick={reset}>
          <RotateCcw />
          Reset
        </Button>
      </div>
    </header>
  );
}
