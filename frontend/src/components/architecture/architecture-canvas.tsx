"use client";

import { motion, AnimatePresence } from "motion/react";
import { NodeCard } from "@/components/architecture/node-card";
import { FlowArrow } from "@/components/architecture/edge-layer";
import { StatusBadge } from "@/components/common/status-badge";
import { usePlatform } from "@/providers/platform-provider";
import {
  getArchitectureEdges,
  getActiveTrace,
  getLatestAuditorRun,
  isDomainLive,
} from "@/lib/state/selectors";
import type { DomainState } from "@/lib/types";
import { cn } from "@/lib/utils";

const RECAP = [
  "Independent domains",
  "Central orchestration",
  "Dynamic discovery",
  "Targeted evals",
  "Independent auditor",
  "Closed-world reachability",
  "Observability",
  "Failure isolation",
];

export function ArchitectureCanvas() {
  const { state, animate, currentStep } = usePlatform();
  const rewards = state.domains.rewards;
  const transactions = state.domains.transactions;
  const isolate =
    rewards.status === "unavailable" || transactions.status === "unavailable";
  const trace = getActiveTrace(state);
  const edges = getArchitectureEdges(state);
  const auditorRun = getLatestAuditorRun(state);
  const activeDomainIds = new Set(
    trace?.spans.map((span) => span.domainId).filter(Boolean),
  );
  const activeTools = new Set(
    trace?.spans.filter((span) => span.kind === "tool").map((span) => span.toolName),
  );

  const edgeById = Object.fromEntries(edges.map((edge) => [edge.id, edge]));
  const userCentral = edgeById["struct-user-central"];
  const auditorCentral = edgeById["struct-auditor-central"];
  const centralRewards = edgeById["struct-central-rewards"];
  const centralTransactions = edgeById["struct-central-transactions"];

  const auditorTone =
    state.auditor.status === "ATTESTED"
      ? "healthy"
      : state.auditor.status === "WITHHELD"
        ? "fail"
        : state.auditor.status === "RUNNING"
          ? "change"
          : "offline";

  const auditorLabel =
    state.auditor.status === "idle" ? "Idle" : state.auditor.status;

  const bothDomainsLive =
    (isDomainLive(rewards) || rewards.status === "unavailable") &&
    (isDomainLive(transactions) || transactions.status === "unavailable");

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-2">
        <h2 className="text-sm font-semibold">Architecture / Runtime Flow</h2>
        <p className="font-mono text-[11px] text-muted-foreground">
          {state.central.modelProvider}/{state.central.modelName}
        </p>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        <div className="mx-auto flex w-full max-w-[340px] flex-col items-stretch">
          <NodeCard
            title="User"
            subtitle="Customer channel"
            active={Boolean(trace)}
          >
            <p className="mt-1 text-[11px] text-muted-foreground">Chat request</p>
          </NodeCard>

          <div className="h-9">
            <FlowArrow
              direction="down"
              kind="request"
              active={Boolean(userCentral?.active)}
              live
            />
          </div>

          <NodeCard
            title="Central Planner"
            subtitle="Orchestrator · A2A client"
            status="active"
            active={Boolean(trace) || state.auditor.status === "RUNNING"}
          >
            <p className="mt-1 text-[11px] leading-snug text-muted-foreground">
              Routes discovered capabilities. No domain business logic.
            </p>
          </NodeCard>

          <div className="flex items-center justify-center gap-2 py-1">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                bothDomainsLive
                  ? "bg-status-change/15 text-status-change-foreground"
                  : "bg-muted text-muted-foreground",
              )}
            >
              {bothDomainsLive ? "delegate in parallel" : "delegate"}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="flex min-w-0 flex-col">
              <div className="h-8">
                <FlowArrow
                  direction="down"
                  kind="delegation"
                  active={Boolean(centralRewards?.active)}
                  live={isDomainLive(rewards) || rewards.status === "unavailable"}
                />
              </div>
              <DomainFlowCard
                domain={rewards}
                isolate={isolate}
                active={activeDomainIds.has("rewards")}
                activeTools={activeTools}
              />
            </div>
            <div className="flex min-w-0 flex-col">
              <div className="h-8">
                <FlowArrow
                  direction="down"
                  kind="delegation"
                  active={Boolean(centralTransactions?.active)}
                  live={
                    isDomainLive(transactions) ||
                    transactions.status === "unavailable"
                  }
                />
              </div>
              <DomainFlowCard
                domain={transactions}
                isolate={isolate}
                active={activeDomainIds.has("transactions")}
                activeTools={activeTools}
              />
            </div>
          </div>

          <div className="h-9">
            <FlowArrow
              direction="down"
              kind="audit"
              active={Boolean(auditorCentral?.active)}
              live={state.auditor.status !== "idle"}
            />
          </div>

          <NodeCard
            title="Independent Auditor"
            subtitle="Rule-based · not an LLM"
            active={state.auditor.status === "RUNNING"}
          >
            <div className="mt-1 flex items-center gap-2">
              <StatusBadge tone={auditorTone}>{auditorLabel}</StatusBadge>
            </div>
            <p className="mt-1 text-[11px] leading-snug text-muted-foreground">
              {auditorRun
                ? auditorRun.subject
                : "Attests published manifests vs reachable inventory."}
            </p>
          </NodeCard>
        </div>

        <AnimatePresence>
          {state.architectureCallout ? (
            <motion.div
              initial={animate ? { opacity: 0, y: 6 } : false}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-3 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2"
            >
              <p className="text-xs font-semibold text-primary">
                {state.architectureCallout.title}
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-foreground">
                {state.architectureCallout.body}
              </p>
            </motion.div>
          ) : null}
        </AnimatePresence>

        {currentStep.id === "step_12_summary" ? (
          <ul className="mt-3 grid grid-cols-2 gap-1.5">
            {RECAP.map((item) => (
              <li
                key={item}
                className="rounded-md border border-border bg-muted/50 px-2 py-1.5 text-[11px] font-medium text-foreground"
              >
                {item}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}

function DomainFlowCard({
  domain,
  isolate,
  active,
  activeTools,
}: {
  domain: DomainState;
  isolate: boolean;
  active: boolean;
  activeTools: Set<string | undefined>;
}) {
  const dimmed = domain.status === "offline" || domain.status === "unavailable";

  return (
    <NodeCard
      title={domain.name}
      subtitle={
        domain.status === "offline"
          ? "Not discovered"
          : `${domain.version} · ${domain.bundleHash}`
      }
      status={domain.status}
      isolateHealthy={isolate && domain.status === "active"}
      dimmed={dimmed}
      active={active}
    >
      {domain.tools.length > 0 ? (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {domain.tools.map((tool) => (
            <span
              key={tool.name}
              className={cn(
                "max-w-full truncate rounded-md border px-1 py-0.5 font-mono text-[9px]",
                activeTools.has(tool.name)
                  ? "border-status-healthy/40 bg-status-healthy/15 text-status-healthy-foreground"
                  : "border-border bg-muted text-muted-foreground",
              )}
            >
              {tool.name}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-1.5 text-[11px] text-muted-foreground">No tools</p>
      )}
    </NodeCard>
  );
}
