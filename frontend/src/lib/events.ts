import type {
  ArchitectureCallout,
  AuditorCheck,
  AuditorVerdict,
  ChatMessage,
  DomainId,
  DomainSnapshot,
  EvalCaseResult,
  EvalRunHeader,
  EvalVerdict,
  SkillSnapshot,
  SpanSnapshot,
  SuiteSelection,
  ToolSnapshot,
} from "@/lib/types";

export type PlatformEventType =
  | "DOMAIN_DISCOVERED"
  | "DOMAIN_OFFLINE"
  | "PROMPT_CHANGED"
  | "TOOL_ADDED"
  | "TOOL_REMOVED"
  | "TOOL_SCHEMA_CHANGED"
  | "SKILL_ADDED"
  | "SKILL_REMOVED"
  | "EVAL_STARTED"
  | "EVAL_CASE_PASSED"
  | "EVAL_CASE_FAILED"
  | "EVAL_COMPLETED"
  | "TRACE_STARTED"
  | "AGENT_DELEGATED"
  | "TOOL_CALLED"
  | "LLM_CALLED"
  | "TRACE_COMPLETED"
  | "CHAT_MESSAGE"
  | "CALLOUT_SET"
  | "AUDITOR_STARTED"
  | "AUDITOR_CHECK_PASSED"
  | "AUDITOR_CHECK_FAILED"
  | "AUDITOR_COMPLETED";

type EventBase = {
  id: string;
  ts: string;
};

export type DomainDiscoveredEvent = EventBase & {
  type: "DOMAIN_DISCOVERED";
  domain: DomainSnapshot;
};

export type DomainOfflineEvent = EventBase & {
  type: "DOMAIN_OFFLINE";
  domainId: DomainId;
  reason?: string;
};

export type PromptChangedEvent = EventBase & {
  type: "PROMPT_CHANGED";
  domainId: DomainId;
  fromHash: string;
  toHash: string;
  fromVersion: string;
  toVersion: string;
};

export type ToolAddedEvent = EventBase & {
  type: "TOOL_ADDED";
  domainId: DomainId;
  tool: ToolSnapshot;
};

export type ToolRemovedEvent = EventBase & {
  type: "TOOL_REMOVED";
  domainId: DomainId;
  tool: ToolSnapshot;
};

export type ToolSchemaChangedEvent = EventBase & {
  type: "TOOL_SCHEMA_CHANGED";
  domainId: DomainId;
  toolName: string;
  fromHash: string;
  toHash: string;
};

export type SkillAddedEvent = EventBase & {
  type: "SKILL_ADDED";
  domainId: DomainId;
  skill: SkillSnapshot;
};

export type SkillRemovedEvent = EventBase & {
  type: "SKILL_REMOVED";
  domainId: DomainId;
  skill: SkillSnapshot;
};

export type EvalStartedEvent = EventBase & {
  type: "EVAL_STARTED";
  run: EvalRunHeader;
  selectedSuites: SuiteSelection[];
  totalCases: number;
};

export type EvalCasePassedEvent = EventBase & {
  type: "EVAL_CASE_PASSED";
  runId: string;
  result: EvalCaseResult;
};

export type EvalCaseFailedEvent = EventBase & {
  type: "EVAL_CASE_FAILED";
  runId: string;
  result: EvalCaseResult;
};

export type EvalCompletedEvent = EventBase & {
  type: "EVAL_COMPLETED";
  runId: string;
  verdict: EvalVerdict;
  passedCount?: number;
  failedCount?: number;
};

export type TraceStartedEvent = EventBase & {
  type: "TRACE_STARTED";
  traceId: string;
  query: string;
};

export type AgentDelegatedEvent = EventBase & {
  type: "AGENT_DELEGATED";
  traceId: string;
  span: SpanSnapshot;
};

export type ToolCalledEvent = EventBase & {
  type: "TOOL_CALLED";
  traceId: string;
  span: SpanSnapshot;
};

export type LlmCalledEvent = EventBase & {
  type: "LLM_CALLED";
  traceId: string;
  span: SpanSnapshot;
};

export type TraceCompletedEvent = EventBase & {
  type: "TRACE_COMPLETED";
  traceId: string;
  answer: string;
  durationMs: number;
  status?: "completed" | "degraded";
};

export type ChatMessageEvent = EventBase & {
  type: "CHAT_MESSAGE";
  message: ChatMessage;
};

export type CalloutSetEvent = EventBase & {
  type: "CALLOUT_SET";
  callout?: ArchitectureCallout;
};

export type AuditorStartedEvent = EventBase & {
  type: "AUDITOR_STARTED";
  runId: string;
  subject: string;
  trigger: string;
  domainId?: DomainId;
  evalRunId?: string;
  manifestHash: string;
};

export type AuditorCheckPassedEvent = EventBase & {
  type: "AUDITOR_CHECK_PASSED";
  runId: string;
  check: AuditorCheck;
};

export type AuditorCheckFailedEvent = EventBase & {
  type: "AUDITOR_CHECK_FAILED";
  runId: string;
  check: AuditorCheck;
};

export type AuditorCompletedEvent = EventBase & {
  type: "AUDITOR_COMPLETED";
  runId: string;
  verdict: AuditorVerdict;
};

export type PlatformEvent =
  | DomainDiscoveredEvent
  | DomainOfflineEvent
  | PromptChangedEvent
  | ToolAddedEvent
  | ToolRemovedEvent
  | ToolSchemaChangedEvent
  | SkillAddedEvent
  | SkillRemovedEvent
  | EvalStartedEvent
  | EvalCasePassedEvent
  | EvalCaseFailedEvent
  | EvalCompletedEvent
  | TraceStartedEvent
  | AgentDelegatedEvent
  | ToolCalledEvent
  | LlmCalledEvent
  | TraceCompletedEvent
  | ChatMessageEvent
  | CalloutSetEvent
  | AuditorStartedEvent
  | AuditorCheckPassedEvent
  | AuditorCheckFailedEvent
  | AuditorCompletedEvent;
