"use client";

import { EmptyState } from "@/components/common/empty-state";
import { SequenceStage } from "@/components/activity/sequence-stage";
import { StatusBadge } from "@/components/common/status-badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePlatform } from "@/providers/platform-provider";
import { getLatestAuditorRun, getLatestEvalRun } from "@/lib/state/selectors";
import { cn } from "@/lib/utils";

function auditorTone(verdict?: string) {
  if (verdict === "ATTESTED") return "healthy" as const;
  if (verdict === "WITHHELD") return "fail" as const;
  if (verdict === "RUNNING") return "change" as const;
  return "offline" as const;
}

export function AuditorPanel() {
  const { state } = usePlatform();
  const run = getLatestAuditorRun(state);
  const evalRun = getLatestEvalRun(state);

  if (!run) {
    return (
      <EmptyState
        title="Independent auditor idle"
        description="When a domain publishes a bundle, this non-LLM service compares the Agent Card to what central can actually reach, and checks that required evals ran against that manifest."
      />
    );
  }

  const passed = run.checks.filter((check) => check.passed).length;

  return (
    <ScrollArea className="h-full">
      <div className="pr-3">
        <p className="mb-4 text-xs text-muted-foreground">
          This auditor is not an LLM. It runs after Central’s evals. Numbered
          stages are sequential; the four control checks in stage 2 run{" "}
          <span className="font-semibold text-status-change-foreground">
            in parallel
          </span>
          .
        </p>
        <ol>
          <SequenceStage
            step={1}
            mode="sequence"
            title="Receive the tested manifest"
            subtitle="Central finished evals against a specific bundle hash. The auditor does not trust a domain-declared change type."
          >
            <div className="rounded-lg border border-border bg-background px-3 py-2">
              <p className="text-sm font-semibold">{run.subject}</p>
              <p className="font-mono text-[11px] text-muted-foreground">
                Method: hash + set compare · manifest {run.manifestHash}
                {run.evalRunId ? ` · eval ${run.evalRunId}` : ""}
              </p>
              {evalRun ? (
                <p className="mt-1 text-xs text-muted-foreground">
                  Linked eval: {evalRun.changeSummary} ({evalRun.verdict})
                </p>
              ) : null}
            </div>
          </SequenceStage>

          <SequenceStage
            step={2}
            mode="parallel"
            title="Run control checks"
            subtitle="These four checks are independent and execute together. Any failure withholds attestation."
          >
            {run.checks.map((check) => (
              <div
                key={check.id}
                className={cn(
                  "rounded-lg border px-3 py-2",
                  check.passed
                    ? "border-border bg-background"
                    : "border-status-fail/30 bg-status-fail/5",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{check.name}</p>
                  <span
                    className={cn(
                      "text-[11px] font-semibold uppercase",
                      check.passed
                        ? "text-status-healthy-foreground"
                        : "text-status-fail-foreground",
                    )}
                  >
                    {check.passed ? "pass" : "fail"}
                  </span>
                </div>
                <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                  {check.method}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-foreground">
                  {check.detail}
                </p>
              </div>
            ))}
          </SequenceStage>

          <SequenceStage
            step={3}
            mode="sequence"
            title="Attest or withhold"
            subtitle="The domain is only trusted if every parallel check passed against the same manifest Central evaluated."
            last
          >
            <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2">
              <StatusBadge tone={auditorTone(run.verdict)}>
                {run.verdict}
              </StatusBadge>
              <span className="text-sm">
                {passed} / {run.checks.length} checks passed
              </span>
            </div>
          </SequenceStage>
        </ol>
      </div>
    </ScrollArea>
  );
}
