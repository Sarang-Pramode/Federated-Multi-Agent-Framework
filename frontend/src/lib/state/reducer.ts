import type { PlatformEvent } from "@/lib/events";
import { explainEvent } from "@/lib/explain";
import type {
  ChangeFeedItem,
  DomainId,
  DomainState,
  EvalRun,
  AuditorRun,
  SystemState,
  TraceSnapshot,
} from "@/lib/types";
import { createInitialState } from "@/lib/state/initial-state";

function pushChange(
  state: SystemState,
  event: PlatformEvent,
  summary: string,
  domainId?: DomainId,
): ChangeFeedItem[] {
  const explained = explainEvent(event);
  const item: ChangeFeedItem = {
    id: `change-${event.id}`,
    timestamp: event.ts,
    eventType: event.type,
    summary,
    technical: explained.technical,
    explanation: explained.explanation,
    domainId,
  };
  return [...state.changes, item];
}

function updateDomain(
  state: SystemState,
  domainId: DomainId,
  patch: Partial<DomainState>,
): SystemState {
  const current = state.domains[domainId];
  return {
    ...state,
    domains: {
      ...state.domains,
      [domainId]: { ...current, ...patch },
    },
  };
}

function upsertTrace(
  traces: TraceSnapshot[],
  traceId: string,
  updater: (trace: TraceSnapshot) => TraceSnapshot,
): TraceSnapshot[] {
  const index = traces.findIndex((trace) => trace.id === traceId);
  if (index === -1) return traces;
  const next = [...traces];
  next[index] = updater(traces[index]);
  return next;
}

function upsertEval(
  runs: EvalRun[],
  runId: string,
  updater: (run: EvalRun) => EvalRun,
): EvalRun[] {
  const index = runs.findIndex((run) => run.id === runId);
  if (index === -1) return runs;
  const next = [...runs];
  next[index] = updater(runs[index]);
  return next;
}

function upsertAuditor(
  runs: AuditorRun[],
  runId: string,
  updater: (run: AuditorRun) => AuditorRun,
): AuditorRun[] {
  const index = runs.findIndex((run) => run.id === runId);
  if (index === -1) return runs;
  const next = [...runs];
  next[index] = updater(runs[index]);
  return next;
}

export function applyEvent(
  state: SystemState,
  event: PlatformEvent,
): SystemState {
  switch (event.type) {
    case "DOMAIN_DISCOVERED": {
      const discovered = event.domain;
      return {
        ...updateDomain(state, discovered.id, {
          ...discovered,
          status: "active",
          latestChange: `Discovered ${discovered.name} ${discovered.version}`,
          latestEvalStatus: state.domains[discovered.id].latestEvalStatus,
        }),
        changes: pushChange(
          state,
          event,
          `${discovered.name} discovered (${discovered.version})`,
          discovered.id,
        ),
      };
    }

    case "DOMAIN_OFFLINE": {
      const domain = state.domains[event.domainId];
      return {
        ...updateDomain(state, event.domainId, {
          status: "unavailable",
          latestChange: event.reason ?? `${domain.name} unavailable`,
        }),
        changes: pushChange(
          state,
          event,
          `${domain.name} unavailable`,
          event.domainId,
        ),
      };
    }

    case "PROMPT_CHANGED": {
      const domain = state.domains[event.domainId];
      return {
        ...updateDomain(state, event.domainId, {
          promptVersion: event.toVersion,
          promptHash: event.toHash,
          version: event.toVersion,
          latestChange: `Prompt ${event.fromHash} → ${event.toHash}`,
        }),
        changes: pushChange(
          state,
          event,
          `${domain.name} prompt changed ${event.fromVersion} → ${event.toVersion}`,
          event.domainId,
        ),
      };
    }

    case "TOOL_ADDED": {
      const domain = state.domains[event.domainId];
      const exists = domain.tools.some((tool) => tool.name === event.tool.name);
      return {
        ...updateDomain(state, event.domainId, {
          tools: exists ? domain.tools : [...domain.tools, event.tool],
          latestChange: `Tool added: ${event.tool.name}`,
        }),
        changes: pushChange(
          state,
          event,
          `Tool added: ${event.tool.name}`,
          event.domainId,
        ),
      };
    }

    case "TOOL_REMOVED": {
      const domain = state.domains[event.domainId];
      return {
        ...updateDomain(state, event.domainId, {
          tools: domain.tools.filter((tool) => tool.name !== event.tool.name),
          latestChange: `Tool removed: ${event.tool.name}`,
        }),
        changes: pushChange(
          state,
          event,
          `Tool removed: ${event.tool.name}`,
          event.domainId,
        ),
      };
    }

    case "TOOL_SCHEMA_CHANGED": {
      const domain = state.domains[event.domainId];
      return {
        ...updateDomain(state, event.domainId, {
          tools: domain.tools.map((tool) =>
            tool.name === event.toolName
              ? { ...tool, schemaHash: event.toHash }
              : tool,
          ),
          latestChange: `Tool schema changed: ${event.toolName}`,
        }),
        changes: pushChange(
          state,
          event,
          `Tool schema changed: ${event.toolName} ${event.fromHash} → ${event.toHash}`,
          event.domainId,
        ),
      };
    }

    case "SKILL_ADDED": {
      const domain = state.domains[event.domainId];
      const exists = domain.skills.some((skill) => skill.id === event.skill.id);
      return {
        ...updateDomain(state, event.domainId, {
          skills: exists ? domain.skills : [...domain.skills, event.skill],
          latestChange: `Capability added: ${event.skill.id}`,
        }),
        changes: pushChange(
          state,
          event,
          `Capability added: ${event.skill.id}`,
          event.domainId,
        ),
      };
    }

    case "SKILL_REMOVED": {
      const domain = state.domains[event.domainId];
      return {
        ...updateDomain(state, event.domainId, {
          skills: domain.skills.filter((skill) => skill.id !== event.skill.id),
          latestChange: `Capability removed: ${event.skill.id}`,
        }),
        changes: pushChange(
          state,
          event,
          `Capability removed: ${event.skill.id}`,
          event.domainId,
        ),
      };
    }

    case "EVAL_STARTED": {
      const run: EvalRun = {
        ...event.run,
        selectedSuites: event.selectedSuites,
        results: [],
        verdict: "RUNNING",
        passedCount: 0,
        failedCount: 0,
        totalCases: event.totalCases,
      };
      const domainId = event.run.affectedDomainId;
      const next = domainId
        ? updateDomain(state, domainId, { latestEvalStatus: "pending" })
        : state;
      return {
        ...next,
        evalRuns: [...state.evalRuns, run],
        activeEvalRunId: run.id,
        changes: pushChange(
          state,
          event,
          `Eval suite triggered (${event.selectedSuites.length} suites)`,
          domainId,
        ),
      };
    }

    case "EVAL_CASE_PASSED":
    case "EVAL_CASE_FAILED": {
      return {
        ...state,
        evalRuns: upsertEval(state.evalRuns, event.runId, (run) => {
          const results = [...run.results, event.result];
          const passedCount = results.filter((result) => result.passed).length;
          const failedCount = results.length - passedCount;
          return { ...run, results, passedCount, failedCount };
        }),
      };
    }

    case "EVAL_COMPLETED": {
      const completed = state.evalRuns.find((run) => run.id === event.runId);
      const passedCount =
        event.passedCount ?? completed?.passedCount ?? 0;
      const failedCount =
        event.failedCount ?? completed?.failedCount ?? 0;
      const domainId = completed?.affectedDomainId;
      const next = domainId
        ? updateDomain(state, domainId, {
            latestEvalStatus:
              event.verdict === "REGRESSION_DETECTED" ? "fail" : "pass",
          })
        : state;
      return {
        ...next,
        evalRuns: upsertEval(state.evalRuns, event.runId, (run) => ({
          ...run,
          verdict: event.verdict,
          passedCount,
          failedCount,
        })),
        releaseStatus:
          event.verdict === "REGRESSION_DETECTED"
            ? "REGRESSION_DETECTED"
            : "passing",
        changes: pushChange(
          state,
          event,
          event.verdict === "REGRESSION_DETECTED"
            ? `${passedCount} passed / ${failedCount} failed`
            : `${passedCount} / ${passedCount + failedCount} passed`,
          domainId,
        ),
      };
    }

    case "TRACE_STARTED": {
      const trace: TraceSnapshot = {
        id: event.traceId,
        query: event.query,
        spans: [],
        status: "running",
      };
      return {
        ...state,
        traces: [...state.traces, trace],
        activeTraceId: event.traceId,
      };
    }

    case "AGENT_DELEGATED":
    case "TOOL_CALLED":
    case "LLM_CALLED": {
      return {
        ...state,
        traces: upsertTrace(state.traces, event.traceId, (trace) => ({
          ...trace,
          spans: [...trace.spans, event.span],
        })),
      };
    }

    case "TRACE_COMPLETED": {
      return {
        ...state,
        traces: upsertTrace(state.traces, event.traceId, (trace) => ({
          ...trace,
          answer: event.answer,
          durationMs: event.durationMs,
          status: event.status ?? "completed",
        })),
      };
    }

    case "CHAT_MESSAGE": {
      return {
        ...state,
        customerMessages: [...state.customerMessages, event.message],
      };
    }

    case "CALLOUT_SET": {
      return {
        ...state,
        architectureCallout: event.callout,
      };
    }

    case "AUDITOR_STARTED": {
      const run: AuditorRun = {
        id: event.runId,
        subject: event.subject,
        trigger: event.trigger,
        domainId: event.domainId,
        evalRunId: event.evalRunId,
        manifestHash: event.manifestHash,
        checks: [],
        verdict: "RUNNING",
      };
      return {
        ...state,
        auditor: {
          status: "RUNNING",
          runs: [...state.auditor.runs, run],
          activeRunId: run.id,
        },
        changes: pushChange(
          state,
          event,
          `Auditor started: ${event.subject}`,
          event.domainId,
        ),
      };
    }

    case "AUDITOR_CHECK_PASSED":
    case "AUDITOR_CHECK_FAILED": {
      return {
        ...state,
        auditor: {
          ...state.auditor,
          runs: upsertAuditor(state.auditor.runs, event.runId, (run) => ({
            ...run,
            checks: [...run.checks, event.check],
          })),
        },
      };
    }

    case "AUDITOR_COMPLETED": {
      return {
        ...state,
        auditor: {
          status: event.verdict,
          activeRunId: event.runId,
          runs: upsertAuditor(state.auditor.runs, event.runId, (run) => ({
            ...run,
            verdict: event.verdict,
          })),
        },
        changes: pushChange(
          state,
          event,
          event.verdict === "ATTESTED"
            ? "Auditor attested the published manifest"
            : "Auditor withheld attestation",
        ),
      };
    }

    default: {
      const _exhaustive: never = event;
      return _exhaustive;
    }
  }
}

export function applyEvents(
  events: PlatformEvent[],
  state: SystemState = createInitialState(),
): SystemState {
  return events.reduce(applyEvent, state);
}

export function eventsThroughStep(
  steps: { events: PlatformEvent[] }[],
  stepIndex: number,
): PlatformEvent[] {
  return steps.slice(0, stepIndex + 1).flatMap((step) => step.events);
}
