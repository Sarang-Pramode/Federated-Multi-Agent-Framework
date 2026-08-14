"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePlatform } from "@/providers/platform-provider";

export function PresenterFooter() {
  const {
    currentStep,
    stepIndex,
    stepCount,
    next,
    back,
    isAnimating,
    mode,
  } = usePlatform();

  const atStart = stepIndex <= 0;
  const atEnd = stepIndex >= stepCount - 1;

  return (
    <footer className="shrink-0 border-t border-border bg-card px-5 py-2.5">
      <div className="flex items-center gap-6">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium uppercase tracking-[0.12em] text-primary">
              Step {stepIndex + 1} of {stepCount}
            </span>
            <span className="truncate text-xs text-muted-foreground">
              {currentStep.concept}
            </span>
          </div>
          <p className="mt-0.5 max-w-4xl text-sm leading-snug text-foreground">
            <span className="font-semibold">{currentStep.title}. </span>
            <span className="text-muted-foreground">{currentStep.explanation}</span>
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            variant="outline"
            onClick={back}
            disabled={mode !== "demo" || atStart}
          >
            <ChevronLeft />
            Back
          </Button>
          <Button onClick={next} disabled={mode !== "demo" || (atEnd && !isAnimating)}>
            {isAnimating ? "Skip animation" : atEnd ? "Done" : "Next"}
            {isAnimating ? null : <ChevronRight />}
          </Button>
        </div>
      </div>
    </footer>
  );
}
