"use client";

import { EmptyState } from "@/components/common/empty-state";
import { SequenceStage } from "@/components/activity/sequence-stage";
import { evalTone, StatusBadge } from "@/components/common/status-badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePlatform } from "@/providers/platform-provider";
import { getLatestEvalRun } from "@/lib/state/selectors";
import { cn } from "@/lib/utils";

const SCENARIO_ORIGIN: Record<string, string> = {
  AGENT_ADDED:
    "AGENT_ADDED maps to frozen intent/routing plus domain smoke tests. Central owns the mapping. The domain does not choose which tests run.",
  PROMPT_CHANGED:
    "PROMPT_CHANGED maps to intent, domain regression, affected cross-domain journeys, and a response judge. Ground truth lives in local JSON, not in the domain repo.",
  TOOL_ADDED:
    "TOOL_ADDED maps to tool-selection evals and existing domain cases so new tools cannot silently steal old questions.",
  SKILL_ADDED:
    "SKILL_ADDED maps to routing plus a capability smoke test for the new customer question.",
};

export function EvalPanel() {
  const { state } = usePlatform();
  const run = getLatestEvalRun(state);

  if (!run) {
    return (
      <EmptyState
        title="No evaluation run"
        description="When a domain comes online or changes a bundle, central selects targeted suites from a deterministic change→test map."
      />
    );
  }

  const origin =
    SCENARIO_ORIGIN[run.trigger] ??
    "Central selected these suites from the change type. Domain teams do not identify blast radius.";

  const bySuite = run.selectedSuites.map((suite) => ({
    suite,
    cases: run.results.filter((result) => result.suiteId === suite.suiteId),
  }));

  return (
    <ScrollArea className="h-full">
      <div className="pr-3">
        <p className="mb-4 text-xs text-muted-foreground">
          Numbered stages run top to bottom. Yellow{" "}
          <span className="font-semibold text-status-change-foreground">
            in parallel
          </span>{" "}
          means those cases execute at the same time after the previous stage
          finishes.
        </p>
        <ol>
          <SequenceStage
            step={1}
            mode="sequence"
            title="Central sees a published change"
            subtitle="Domain self-tests before publish are not shown. The controller only reacts to the Agent Card."
          >
            <div className="rounded-lg border border-border bg-background px-3 py-2">
              <p className="text-sm font-semibold">{run.changeSummary}</p>
              <p className="font-mono text-[11px] text-muted-foreground">
                Trigger {run.trigger}
              </p>
            </div>
          </SequenceStage>

          <SequenceStage
            step={2}
            mode="sequence"
            title="Change type selects frozen suites"
            subtitle={origin}
          >
            {run.selectedSuites.map((suite) => (
              <div
                key={suite.suiteId}
                className="rounded-md border border-border bg-background px-2.5 py-1.5"
              >
                <p className="text-xs font-medium">{suite.suiteName}</p>
                <p className="text-[11px] leading-relaxed text-muted-foreground">
                  {suite.reason}
                </p>
              </div>
            ))}
          </SequenceStage>

          <SequenceStage
            step={3}
            mode="parallel"
            title="Execute selected cases"
            subtitle="Suites run side by side against the published manifest. Cases inside a suite are independent."
          >
            {bySuite.map(({ suite, cases }) => {
              const passed = cases.filter((item) => item.passed).length;
              return (
                <div
                  key={suite.suiteId}
                  className="rounded-lg border border-border bg-background px-3 py-2"
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="text-xs font-semibold">{suite.suiteName}</p>
                    <p className="font-mono text-[11px] text-muted-foreground">
                      {passed}/{cases.length}
                    </p>
                  </div>
                  <ul className="mt-1.5 space-y-1">
                    {cases.map((result) => (
                      <li
                        key={result.id}
                        className="flex items-center justify-between gap-2 text-xs"
                      >
                        <span className="truncate">{result.name}</span>
                        <span
                          className={cn(
                            "shrink-0 font-medium",
                            result.passed
                              ? "text-status-healthy-foreground"
                              : "text-status-fail-foreground",
                          )}
                        >
                          {result.passed ? "PASS" : "FAIL"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </SequenceStage>

          <SequenceStage
            step={4}
            mode="sequence"
            title="Score the run"
            subtitle="Central waits for every parallel suite before recording a verdict."
          >
            {run.results
              .filter((result) => !result.passed)
              .map((result) => (
                <div
                  key={result.id}
                  className="rounded-lg border border-status-fail/30 bg-status-fail/5 px-3 py-2"
                >
                  <p className="text-sm font-semibold">{result.name}</p>
                  <p className="mt-1 text-xs">
                    <span className="text-muted-foreground">Expected: </span>
                    {result.expected}
                  </p>
                  <p className="text-xs">
                    <span className="text-muted-foreground">Actual: </span>
                    {result.actual}
                  </p>
                  {result.reason ? (
                    <p className="mt-1 text-xs text-status-fail-foreground">
                      {result.reason}
                    </p>
                  ) : null}
                </div>
              ))}
            <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2">
              <StatusBadge tone={evalTone(run.verdict)}>{run.verdict}</StatusBadge>
              <p className="text-sm">
                <span className="font-semibold">
                  {run.passedCount} / {run.totalCases} passed
                </span>
                {run.failedCount > 0 ? (
                  <span className="text-status-fail-foreground">
                    {" "}
                    · {run.failedCount} failed
                  </span>
                ) : null}
              </p>
            </div>
          </SequenceStage>

          <SequenceStage
            step={5}
            mode="sequence"
            title="Hand the tested manifest to the auditor"
            subtitle="A passing or failing eval is not the last word. The independent auditor still verifies reachability and that these evals ran against this bundle."
            last
          />
        </ol>
      </div>
    </ScrollArea>
  );
}
