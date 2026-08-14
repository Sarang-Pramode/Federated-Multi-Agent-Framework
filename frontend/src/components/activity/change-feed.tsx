"use client";

import { useMemo, useState } from "react";
import { EmptyState } from "@/components/common/empty-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePlatform } from "@/providers/platform-provider";
import type { ChangeFeedItem } from "@/lib/types";
import { cn } from "@/lib/utils";

const TRIGGERS = new Set([
  "DOMAIN_DISCOVERED",
  "DOMAIN_OFFLINE",
  "PROMPT_CHANGED",
  "TOOL_ADDED",
  "TOOL_REMOVED",
  "TOOL_SCHEMA_CHANGED",
  "SKILL_ADDED",
  "SKILL_REMOVED",
]);

type Episode = {
  id: string;
  timestamp: string;
  trigger: ChangeFeedItem;
  evalStart?: ChangeFeedItem;
  evalComplete?: ChangeFeedItem;
  auditorStart?: ChangeFeedItem;
  auditorComplete?: ChangeFeedItem;
};

function groupEpisodes(items: ChangeFeedItem[]): Episode[] {
  const episodes: Episode[] = [];
  let current: Episode | undefined;

  for (const item of items) {
    if (TRIGGERS.has(item.eventType)) {
      current = { id: item.id, timestamp: item.timestamp, trigger: item };
      episodes.push(current);
      continue;
    }
    if (!current) {
      current = { id: item.id, timestamp: item.timestamp, trigger: item };
      episodes.push(current);
      continue;
    }
    if (item.eventType === "EVAL_STARTED") current.evalStart = item;
    else if (item.eventType === "EVAL_COMPLETED") current.evalComplete = item;
    else if (item.eventType === "AUDITOR_STARTED") current.auditorStart = item;
    else if (item.eventType === "AUDITOR_COMPLETED") current.auditorComplete = item;
    else {
      current = { id: item.id, timestamp: item.timestamp, trigger: item };
      episodes.push(current);
    }
  }

  return episodes;
}

function outcome(episode: Episode): { label: string; tone: "healthy" | "fail" | "change" | "offline" | "neutral" } {
  const audit = episode.auditorComplete?.summary ?? "";
  const evalSummary = episode.evalComplete?.summary ?? "";
  if (episode.trigger.eventType === "DOMAIN_OFFLINE") {
    return { label: "Isolated", tone: "offline" };
  }
  if (audit.includes("withheld") || evalSummary.includes("failed")) {
    return { label: "Blocked", tone: "fail" };
  }
  if (audit.includes("attested")) {
    return { label: "Attested", tone: "healthy" };
  }
  if (evalSummary.includes("passed")) {
    return { label: "Eval pass", tone: "healthy" };
  }
  if (episode.evalStart || episode.auditorStart) {
    return { label: "Running", tone: "change" };
  }
  return { label: "Detected", tone: "neutral" };
}

function domainLabel(id?: string) {
  if (id === "rewards") return "Rewards";
  if (id === "transactions") return "Transactions";
  return id;
}

type PipelineStep = {
  key: string;
  label: string;
  summary: string;
  eventType: string;
  item: ChangeFeedItem;
};

function pipelineSteps(episode: Episode): PipelineStep[] {
  const steps: PipelineStep[] = [
    {
      key: "change",
      label: "Change detected",
      summary: episode.trigger.summary,
      eventType: episode.trigger.eventType,
      item: episode.trigger,
    },
  ];

  const evalItem = episode.evalComplete ?? episode.evalStart;
  if (evalItem) {
    steps.push({
      key: "eval",
      label: "Targeted evals",
      summary: evalItem.summary,
      eventType: evalItem.eventType,
      item: evalItem,
    });
  }

  const auditorItem = episode.auditorComplete ?? episode.auditorStart;
  if (auditorItem) {
    steps.push({
      key: "audit",
      label: "Independent auditor",
      summary: auditorItem.summary,
      eventType: auditorItem.eventType,
      item: auditorItem,
    });
  }

  return steps;
}

export function ChangeFeed() {
  const { state } = usePlatform();
  const [openId, setOpenId] = useState<string | null>(null);
  const episodes = useMemo(
    () => groupEpisodes(state.changes).reverse(),
    [state.changes],
  );

  if (episodes.length === 0) {
    return (
      <EmptyState
        title="No changes yet"
        description="Discovery, prompt, tool, and skill events will land here."
      />
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="pr-3">
        <p className="mb-4 text-xs text-muted-foreground">
          Newest first. Each card is one published change. Steps inside a card
          run{" "}
          <span className="font-semibold text-foreground">in sequence</span>
          {" — "}
          detect, evaluate, then audit. Parallel suite execution is on the
          Evaluation and Auditor tabs.
        </p>
        <ol className="space-y-3">
          {episodes.map((episode) => {
            const open = openId === episode.id;
            const result = outcome(episode);
            const steps = pipelineSteps(episode);
            const domain = domainLabel(episode.trigger.domainId);

            return (
              <li key={episode.id}>
                <article
                  className={cn(
                    "rounded-xl border px-4 py-3 transition-colors",
                    open
                      ? "border-primary/30 bg-primary/5"
                      : "border-border bg-background",
                  )}
                >
                  <button
                    type="button"
                    onClick={() => setOpenId(open ? null : episode.id)}
                    className="flex w-full items-start justify-between gap-3 text-left"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
                          {episode.timestamp}
                        </span>
                        {domain ? (
                          <span className="text-[11px] font-medium text-muted-foreground">
                            {domain}
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1.5 text-sm font-semibold text-foreground">
                        {episode.trigger.summary}
                      </p>
                    </div>
                    <StatusBadge tone={result.tone}>{result.label}</StatusBadge>
                  </button>

                  <ol className="mt-3">
                    {steps.map((step, index) => {
                      const last = index === steps.length - 1;
                      return (
                        <li key={step.key} className="flex gap-3">
                          <div className="flex w-4 shrink-0 flex-col items-center">
                            <span
                              className={cn(
                                "mt-1 size-2.5 rounded-full",
                                step.key === "audit"
                                  ? "bg-status-change"
                                  : step.key === "eval"
                                    ? "bg-status-healthy"
                                    : "bg-primary",
                              )}
                            />
                            {last ? null : (
                              <span className="mt-1 w-px flex-1 min-h-5 bg-border" />
                            )}
                          </div>
                          <div className={cn("min-w-0 flex-1", last ? "pb-0" : "pb-3")}>
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-xs font-semibold">
                                {index + 1}. {step.label}
                              </span>
                              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                                in sequence
                              </span>
                            </div>
                            <p className="mt-0.5 text-sm text-foreground">
                              {step.summary}
                            </p>
                            <p className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
                              {step.eventType}
                            </p>
                          </div>
                        </li>
                      );
                    })}
                  </ol>

                  {open ? (
                    <div className="mt-3 space-y-2 border-t border-border pt-3">
                      {steps.map((step) => (
                        <div key={`${step.key}-detail`}>
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                            {step.label}
                          </p>
                          <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                            {step.item.technical}
                          </p>
                          <p className="mt-0.5 text-xs leading-relaxed text-foreground">
                            {step.item.explanation}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </article>
              </li>
            );
          })}
        </ol>
      </div>
    </ScrollArea>
  );
}
