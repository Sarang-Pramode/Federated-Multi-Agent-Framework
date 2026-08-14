export type DomainId = "rewards" | "transactions";

export type DomainStatus =
  | "offline"
  | "active"
  | "unavailable"
  | "healthy";

export type EvalVerdict = "PASS" | "REGRESSION_DETECTED" | "RUNNING";

export type ReleaseStatus = "stable" | "REGRESSION_DETECTED" | "passing";

export type AuditorVerdict = "ATTESTED" | "WITHHELD" | "RUNNING";

export type SpanKind =
  | "planner"
  | "delegation"
  | "agent_loop"
  | "tool"
  | "llm"
  | "final";

export type SpanStatus = "ok" | "error" | "degraded";

export type SkillSnapshot = {
  id: string;
  name: string;
  description: string;
  allowedTools: string[];
  version: string;
  enabled: boolean;
};

export type ToolSnapshot = {
  name: string;
  description: string;
  schemaHash: string;
};

export type DomainSnapshot = {
  id: DomainId;
  name: string;
  version: string;
  status: DomainStatus;
  promptVersion: string;
  promptHash: string;
  skills: SkillSnapshot[];
  tools: ToolSnapshot[];
  modelProvider: string;
  modelName: string;
  protocolInterface: string;
  bundleHash: string;
};

export type DomainState = DomainSnapshot & {
  latestChange?: string;
  latestEvalStatus: "pass" | "fail" | "pending" | "none";
};

export type CentralState = {
  name: string;
  status: "active";
  modelProvider: string;
  modelName: string;
};

export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
};

export type SpanSnapshot = {
  id: string;
  parentId?: string;
  kind: SpanKind;
  label: string;
  domainId?: DomainId;
  toolName?: string;
  startMs: number;
  durationMs: number;
  status?: SpanStatus;
};

export type TraceSnapshot = {
  id: string;
  query: string;
  spans: SpanSnapshot[];
  answer?: string;
  durationMs?: number;
  status: "running" | "completed" | "degraded";
};

export type EvalCaseResult = {
  id: string;
  suiteId: string;
  name: string;
  expected: string;
  actual: string;
  reason?: string;
  passed: boolean;
};

export type SuiteSelection = {
  suiteId: string;
  suiteName: string;
  reason: string;
};

export type EvalRunHeader = {
  id: string;
  trigger: string;
  changeSummary: string;
  affectedDomainId?: DomainId;
};

export type EvalRun = EvalRunHeader & {
  selectedSuites: SuiteSelection[];
  results: EvalCaseResult[];
  verdict: EvalVerdict;
  passedCount: number;
  failedCount: number;
  totalCases: number;
};

export type ChangeFeedItem = {
  id: string;
  timestamp: string;
  eventType: string;
  summary: string;
  technical: string;
  explanation: string;
  domainId?: DomainId;
};

export type ArchitectureCallout = {
  title: string;
  body: string;
};

export type AuditorCheck = {
  id: string;
  name: string;
  method: "hash-compare" | "set-compare" | "rule";
  expected: string;
  actual: string;
  passed: boolean;
  detail: string;
};

export type AuditorRun = {
  id: string;
  subject: string;
  trigger: string;
  domainId?: DomainId;
  evalRunId?: string;
  manifestHash: string;
  checks: AuditorCheck[];
  verdict: AuditorVerdict;
};

export type AuditorState = {
  status: "idle" | AuditorVerdict;
  runs: AuditorRun[];
  activeRunId?: string;
};

export type SystemState = {
  central: CentralState;
  domains: Record<DomainId, DomainState>;
  changes: ChangeFeedItem[];
  traces: TraceSnapshot[];
  evalRuns: EvalRun[];
  auditor: AuditorState;
  customerMessages: ChatMessage[];
  releaseStatus: ReleaseStatus;
  activeTraceId?: string;
  activeEvalRunId?: string;
  architectureCallout?: ArchitectureCallout;
};

export type DemoMode = "demo" | "live";
