import type { DomainId, DomainState, SystemState, TraceSnapshot } from "@/lib/types";

export function getDomainList(state: SystemState): DomainState[] {
  return [state.domains.rewards, state.domains.transactions];
}

export function getActiveTrace(state: SystemState): TraceSnapshot | undefined {
  if (state.activeTraceId) {
    return state.traces.find((trace) => trace.id === state.activeTraceId);
  }
  return state.traces.at(-1);
}

export function getLatestEvalRun(state: SystemState) {
  if (state.activeEvalRunId) {
    return state.evalRuns.find((run) => run.id === state.activeEvalRunId);
  }
  return state.evalRuns.at(-1);
}

export function isDomainLive(domain: DomainState): boolean {
  return domain.status === "active" || domain.status === "healthy";
}

export type ArchitectureEdge = {
  id: string;
  from: "user" | "central" | DomainId | "auditor";
  to: "user" | "central" | DomainId | "auditor";
  domainId?: DomainId;
  toolName?: string;
  active: boolean;
  kind: "request" | "delegation" | "response" | "audit";
};

export function getArchitectureEdges(state: SystemState): ArchitectureEdge[] {
  const trace = getActiveTrace(state);
  const auditorBusy = state.auditor.status === "RUNNING";
  const auditorAttested = state.auditor.status === "ATTESTED";

  const edges: ArchitectureEdge[] = [
    {
      id: "struct-user-central",
      from: "user",
      to: "central",
      active: Boolean(trace),
      kind: "request",
    },
    {
      id: "struct-auditor-central",
      from: "auditor",
      to: "central",
      active:
        auditorBusy ||
        auditorAttested ||
        state.auditor.status === "WITHHELD",
      kind: "audit",
    },
    {
      id: "struct-central-rewards",
      from: "central",
      to: "rewards",
      domainId: "rewards",
      active: Boolean(trace?.spans.some((span) => span.domainId === "rewards")),
      kind: "delegation",
    },
    {
      id: "struct-central-transactions",
      from: "central",
      to: "transactions",
      domainId: "transactions",
      active: Boolean(
        trace?.spans.some((span) => span.domainId === "transactions"),
      ),
      kind: "delegation",
    },
  ];

  return edges;
}

export function getLatestAuditorRun(state: SystemState) {
  if (state.auditor.activeRunId) {
    return state.auditor.runs.find((run) => run.id === state.auditor.activeRunId);
  }
  return state.auditor.runs.at(-1);
}

export function getCapabilityInventory(state: SystemState) {
  return getDomainList(state).flatMap((domain) =>
    domain.skills.map((skill) => ({
      domainId: domain.id,
      domainName: domain.name,
      domainStatus: domain.status,
      skill,
    })),
  );
}

export function getToolInventory(state: SystemState) {
  return getDomainList(state).flatMap((domain) =>
    domain.tools.map((tool) => ({
      domainId: domain.id,
      domainName: domain.name,
      domainStatus: domain.status,
      tool,
    })),
  );
}
