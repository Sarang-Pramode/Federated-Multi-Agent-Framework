import type { PlatformEvent } from "@/lib/events";
import type { SpanSnapshot } from "@/lib/types";
import {
  CROSS_DOMAIN_ANSWER,
  CROSS_DOMAIN_QUERY,
  DEGRADED_CROSS_DOMAIN_ANSWER,
  EXPIRY_ANSWER,
  EXPIRY_QUERY,
  NO_CAPABILITY_ANSWER,
  POINTS_ANSWER,
  POINTS_QUERY,
  PROMPT_HASH,
  BUNDLE_HASH,
  TRANSACTIONS_ONLY_ANSWER,
  TRANSACTIONS_ONLY_QUERY,
  TOTAL_PROMPT_EVAL_CASES,
  TOTAL_TOOL_EVAL_CASES,
  expiringPointsSkill,
  expiringPointsTool,
  manifestAuditorChecks,
  promptChangeSuites,
  promptEvalCasesFail,
  promptEvalCasesPass,
  rewardsDomainV1,
  rewardsOnboardingCases,
  rewardsOnboardingSuites,
  rewardsSkillsV1,
  rewardsToolsV1,
  skillAddedSuites,
  skillOnboardingCases,
  toolAddedSuites,
  toolEvalCases,
  transactionsDomainV1,
  transactionsOnboardingCases,
  transactionsOnboardingSuites,
  transactionsSkills,
  transactionsTools,
} from "@/demo/fixtures";
import type { AuditorCheck, DomainId, EvalCaseResult, SuiteSelection } from "@/lib/types";

export type DemoStepId =
  | "step_1_central_only"
  | "step_2_rewards_discovered"
  | "step_3_rewards_request"
  | "step_4_transactions_discovered"
  | "step_5_cross_domain"
  | "step_6_prompt_changed"
  | "step_7_eval_failure"
  | "step_8_prompt_fixed"
  | "step_9_tool_added"
  | "step_10_skill_added"
  | "step_11_domain_failure"
  | "step_12_summary";

export type DemoStep = {
  id: DemoStepId;
  number: number;
  title: string;
  concept: string;
  explanation: string;
  presenterNote: string;
  exampleQuery?: string;
  events: PlatformEvent[];
};

let eventSeq = 0;
function eid(prefix: string): string {
  eventSeq += 1;
  return `${prefix}-${eventSeq}`;
}

function span(partial: SpanSnapshot): SpanSnapshot {
  return { status: "ok", ...partial };
}

function chat(
  ts: string,
  id: string,
  role: "user" | "assistant",
  content: string,
): PlatformEvent {
  return {
    type: "CHAT_MESSAGE",
    id: eid(id),
    ts,
    message: { id, role, content, timestamp: ts },
  };
}

function evalPipeline(input: {
  prefix: string;
  ts: string;
  runId: string;
  trigger: string;
  changeSummary: string;
  domainId: DomainId;
  suites: SuiteSelection[];
  cases: EvalCaseResult[];
  verdict?: "PASS" | "REGRESSION_DETECTED";
}): PlatformEvent[] {
  const verdict = input.verdict ?? "PASS";
  const passed = input.cases.filter((item) => item.passed).length;
  const failed = input.cases.length - passed;
  return [
    {
      type: "EVAL_STARTED",
      id: eid(input.prefix),
      ts: input.ts,
      run: {
        id: input.runId,
        trigger: input.trigger,
        changeSummary: input.changeSummary,
        affectedDomainId: input.domainId,
      },
      selectedSuites: input.suites,
      totalCases: input.cases.length,
    },
    ...input.cases.map((result) => ({
      type: (result.passed ? "EVAL_CASE_PASSED" : "EVAL_CASE_FAILED") as
        | "EVAL_CASE_PASSED"
        | "EVAL_CASE_FAILED",
      id: eid(input.prefix),
      ts: input.ts,
      runId: input.runId,
      result,
    })),
    {
      type: "EVAL_COMPLETED" as const,
      id: eid(input.prefix),
      ts: input.ts,
      runId: input.runId,
      verdict,
      passedCount: passed,
      failedCount: failed,
    },
  ];
}

function auditorPipeline(input: {
  prefix: string;
  ts: string;
  runId: string;
  subject: string;
  trigger: string;
  domainId: DomainId;
  evalRunId: string;
  manifestHash: string;
  checks: AuditorCheck[];
}): PlatformEvent[] {
  const attested = input.checks.every((check) => check.passed);
  return [
    {
      type: "AUDITOR_STARTED",
      id: eid(input.prefix),
      ts: input.ts,
      runId: input.runId,
      subject: input.subject,
      trigger: input.trigger,
      domainId: input.domainId,
      evalRunId: input.evalRunId,
      manifestHash: input.manifestHash,
    },
    ...input.checks.map((check) => ({
      type: (check.passed ? "AUDITOR_CHECK_PASSED" : "AUDITOR_CHECK_FAILED") as
        | "AUDITOR_CHECK_PASSED"
        | "AUDITOR_CHECK_FAILED",
      id: eid(input.prefix),
      ts: input.ts,
      runId: input.runId,
      check,
    })),
    {
      type: "AUDITOR_COMPLETED" as const,
      id: eid(input.prefix),
      ts: input.ts,
      runId: input.runId,
      verdict: attested ? "ATTESTED" : "WITHHELD",
    },
  ];
}

const step1: DemoStep = {
  id: "step_1_central_only",
  number: 1,
  title: "Central platform only",
  concept: "The runtime can be alive with no domain intelligence connected.",
  explanation:
    "The central runtime is alive, but no domain intelligence is connected. A customer question about points has nowhere to go.",
  presenterNote:
    "Stay on this step long enough for the audience to see both domains offline, then ask the points question so the empty capability story lands.",
  exampleQuery: POINTS_QUERY,
  events: [
    chat("23:00", "m-s1-user", "user", POINTS_QUERY),
    {
      type: "TRACE_STARTED",
      id: eid("s1"),
      ts: "23:00",
      traceId: "tr-s1",
      query: POINTS_QUERY,
    },
    {
      type: "LLM_CALLED",
      id: eid("s1"),
      ts: "23:00",
      traceId: "tr-s1",
      span: span({
        id: "tr-s1-planner",
        kind: "planner",
        label: "Central planner",
        startMs: 0,
        durationMs: 42,
      }),
    },
    {
      type: "TRACE_COMPLETED",
      id: eid("s1"),
      ts: "23:00",
      traceId: "tr-s1",
      answer: NO_CAPABILITY_ANSWER,
      durationMs: 48,
      status: "degraded",
    },
    chat("23:00", "m-s1-asst", "assistant", NO_CAPABILITY_ANSWER),
  ],
};

const step2: DemoStep = {
  id: "step_2_rewards_discovered",
  number: 2,
  title: "Rewards appears — central must evaluate",
  concept: "A newly discovered domain is not trusted until central runs targeted evals and an independent auditor attests the manifest.",
  explanation:
    "Rewards published a bundle. Central did not ship Rewards code — it discovered the Agent Card, selected frozen routing and smoke tests for that change type, then handed the result to a rule-based auditor.",
  presenterNote: "",
  events: [
    {
      type: "DOMAIN_DISCOVERED",
      id: eid("s2"),
      ts: "23:01",
      domain: rewardsDomainV1(),
    },
    ...evalPipeline({
      prefix: "s2",
      ts: "23:01",
      runId: "eval-rewards-onboard",
      trigger: "AGENT_ADDED",
      changeSummary: "New domain: Rewards v1.0",
      domainId: "rewards",
      suites: rewardsOnboardingSuites,
      cases: rewardsOnboardingCases,
    }),
    ...auditorPipeline({
      prefix: "s2",
      ts: "23:01",
      runId: "audit-rewards-v1",
      subject: "Rewards v1.0 published manifest",
      trigger: "AGENT_ADDED",
      domainId: "rewards",
      evalRunId: "eval-rewards-onboard",
      manifestHash: BUNDLE_HASH.rewardsV1,
      checks: manifestAuditorChecks({
        domainName: "Rewards",
        bundleHash: BUNDLE_HASH.rewardsV1,
        publishedSkills: rewardsSkillsV1.map((skill) => skill.id),
        publishedTools: rewardsToolsV1.map((tool) => tool.name),
        reachableSkills: rewardsSkillsV1.map((skill) => skill.id),
        reachableTools: rewardsToolsV1.map((tool) => tool.name),
        requiredSuites: rewardsOnboardingSuites.map((suite) => suite.suiteId),
        selectedSuites: rewardsOnboardingSuites.map((suite) => suite.suiteId),
        evalVerdict: "PASS",
      }),
    }),
    {
      type: "CALLOUT_SET",
      id: eid("s2"),
      ts: "23:01",
      callout: {
        title: "New domain → eval → audit",
        body: "Rewards v1.0 is reachable only after central ran onboarding evals and the auditor attested bundle m-rew-10.",
      },
    },
  ],
};

const step3: DemoStep = {
  id: "step_3_rewards_request",
  number: 3,
  title: "Central can now answer new questions",
  concept: "A newly discovered domain capability expands what the overall system can do.",
  explanation:
    "The same points question now routes User → Central Planner → Rewards → get_points_balance. The central application did not change.",
  presenterNote:
    "Replay the exact same customer sentence from step 1. The only difference is that Rewards is discovered.",
  exampleQuery: POINTS_QUERY,
  events: [
    chat("23:02", "m-s3-user", "user", POINTS_QUERY),
    {
      type: "TRACE_STARTED",
      id: eid("s3"),
      ts: "23:02",
      traceId: "tr-s3",
      query: POINTS_QUERY,
    },
    {
      type: "LLM_CALLED",
      id: eid("s3"),
      ts: "23:02",
      traceId: "tr-s3",
      span: span({
        id: "tr-s3-planner",
        kind: "planner",
        label: "Central planner",
        startMs: 0,
        durationMs: 55,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s3"),
      ts: "23:02",
      traceId: "tr-s3",
      span: span({
        id: "tr-s3-rewards",
        parentId: "tr-s3-planner",
        kind: "delegation",
        label: "Rewards agent",
        domainId: "rewards",
        startMs: 58,
        durationMs: 140,
      }),
    },
    {
      type: "LLM_CALLED",
      id: eid("s3"),
      ts: "23:02",
      traceId: "tr-s3",
      span: span({
        id: "tr-s3-loop",
        parentId: "tr-s3-rewards",
        kind: "agent_loop",
        label: "Rewards reason / act",
        domainId: "rewards",
        startMs: 62,
        durationMs: 48,
      }),
    },
    {
      type: "TOOL_CALLED",
      id: eid("s3"),
      ts: "23:02",
      traceId: "tr-s3",
      span: span({
        id: "tr-s3-tool",
        parentId: "tr-s3-loop",
        kind: "tool",
        label: "get_points_balance",
        domainId: "rewards",
        toolName: "get_points_balance",
        startMs: 112,
        durationMs: 18,
      }),
    },
    {
      type: "TRACE_COMPLETED",
      id: eid("s3"),
      ts: "23:02",
      traceId: "tr-s3",
      answer: POINTS_ANSWER,
      durationMs: 210,
    },
    chat("23:02", "m-s3-asst", "assistant", POINTS_ANSWER),
    {
      type: "CALLOUT_SET",
      id: eid("s3"),
      ts: "23:02",
      callout: {
        title: "Central did not change",
        body: "A newly discovered domain capability expanded what the overall system can do.",
      },
    },
  ],
};

const step4: DemoStep = {
  id: "step_4_transactions_discovered",
  number: 4,
  title: "Transactions appears — same onboarding gate",
  concept: "Every new domain, not just Rewards, is evaluated and audited before it is trusted.",
  explanation:
    "Transactions published its own bundle. Central selected routing plus Transactions smoke tests, then the auditor confirmed the reachable tools match the published card.",
  presenterNote: "",
  events: [
    {
      type: "DOMAIN_DISCOVERED",
      id: eid("s4"),
      ts: "23:03",
      domain: transactionsDomainV1(),
    },
    ...evalPipeline({
      prefix: "s4",
      ts: "23:03",
      runId: "eval-txn-onboard",
      trigger: "AGENT_ADDED",
      changeSummary: "New domain: Transactions v1.0",
      domainId: "transactions",
      suites: transactionsOnboardingSuites,
      cases: transactionsOnboardingCases,
    }),
    ...auditorPipeline({
      prefix: "s4",
      ts: "23:03",
      runId: "audit-txn-v1",
      subject: "Transactions v1.0 published manifest",
      trigger: "AGENT_ADDED",
      domainId: "transactions",
      evalRunId: "eval-txn-onboard",
      manifestHash: BUNDLE_HASH.transactionsV1,
      checks: manifestAuditorChecks({
        domainName: "Transactions",
        bundleHash: BUNDLE_HASH.transactionsV1,
        publishedSkills: transactionsSkills.map((skill) => skill.id),
        publishedTools: transactionsTools.map((tool) => tool.name),
        reachableSkills: transactionsSkills.map((skill) => skill.id),
        reachableTools: transactionsTools.map((tool) => tool.name),
        requiredSuites: transactionsOnboardingSuites.map((suite) => suite.suiteId),
        selectedSuites: transactionsOnboardingSuites.map((suite) => suite.suiteId),
        evalVerdict: "PASS",
      }),
    }),
    {
      type: "CALLOUT_SET",
      id: eid("s4"),
      ts: "23:03",
      callout: {
        title: "Registry updated and attested",
        body: "Transactions v1.0 passed onboarding evals. Auditor attested bundle m-txn-10.",
      },
    },
  ],
};

const step5: DemoStep = {
  id: "step_5_cross_domain",
  number: 5,
  title: "Cross-domain journey",
  concept: "All cross-domain delegation goes through central. Domains do not call each other.",
  explanation:
    "The planner fans out: Transactions fetches Demo Bistro (T1001, $100, restaurant), Rewards applies the 3× multiplier, and the composed answer is 300 points.",
  presenterNote:
    "Walk the trace tree: planner, two delegations, tool calls, final answer. Mention the restaurant 3× rule.",
  exampleQuery: CROSS_DOMAIN_QUERY,
  events: [
    chat("23:04", "m-s5-user", "user", CROSS_DOMAIN_QUERY),
    {
      type: "TRACE_STARTED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      query: CROSS_DOMAIN_QUERY,
    },
    {
      type: "LLM_CALLED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-planner",
        kind: "planner",
        label: "Central planner",
        startMs: 0,
        durationMs: 70,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-txn",
        parentId: "tr-s5-planner",
        kind: "delegation",
        label: "Transactions agent",
        domainId: "transactions",
        startMs: 74,
        durationMs: 90,
      }),
    },
    {
      type: "LLM_CALLED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-txn-loop",
        parentId: "tr-s5-txn",
        kind: "agent_loop",
        label: "Transactions reason / act",
        domainId: "transactions",
        startMs: 78,
        durationMs: 40,
      }),
    },
    {
      type: "TOOL_CALLED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-txn-tool",
        parentId: "tr-s5-txn-loop",
        kind: "tool",
        label: "get_transaction_by_id",
        domainId: "transactions",
        toolName: "get_transaction_by_id",
        startMs: 120,
        durationMs: 22,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-rew",
        parentId: "tr-s5-planner",
        kind: "delegation",
        label: "Rewards agent",
        domainId: "rewards",
        startMs: 168,
        durationMs: 110,
      }),
    },
    {
      type: "LLM_CALLED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-rew-loop",
        parentId: "tr-s5-rew",
        kind: "agent_loop",
        label: "Rewards reason / act",
        domainId: "rewards",
        startMs: 172,
        durationMs: 44,
      }),
    },
    {
      type: "TOOL_CALLED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      span: span({
        id: "tr-s5-rew-tool",
        parentId: "tr-s5-rew-loop",
        kind: "tool",
        label: "calculate_rewards",
        domainId: "rewards",
        toolName: "calculate_rewards",
        startMs: 220,
        durationMs: 26,
      }),
    },
    {
      type: "TRACE_COMPLETED",
      id: eid("s5"),
      ts: "23:04",
      traceId: "tr-s5",
      answer: CROSS_DOMAIN_ANSWER,
      durationMs: 310,
    },
    chat("23:04", "m-s5-asst", "assistant", CROSS_DOMAIN_ANSWER),
    {
      type: "CALLOUT_SET",
      id: eid("s5"),
      ts: "23:04",
      callout: {
        title: "Fan-out through central",
        body: "Transactions found T1001 ($100, restaurant). Rewards applied 3× → 300 points.",
      },
    },
  ],
};

const step6: DemoStep = {
  id: "step_6_prompt_changed",
  number: 6,
  title: "Prompt change detected",
  concept: "Central compares runtime snapshots. Domain teams do not declare the change type.",
  explanation:
    "Rewards independently swapped prompt_good for prompt_bad. The fingerprint moved 8ab1 → 91fd (v1.0 → v1.1), and the platform selected targeted evals for the blast radius.",
  presenterNote:
    "Pause on the hash diff, then on the four selected suites and the why-these-tests copy. Do not skip to the failure yet.",
  events: [
    {
      type: "PROMPT_CHANGED",
      id: eid("s6"),
      ts: "23:05",
      domainId: "rewards",
      fromHash: PROMPT_HASH.good,
      toHash: PROMPT_HASH.bad,
      fromVersion: "1.0",
      toVersion: "1.1",
    },
    {
      type: "EVAL_STARTED",
      id: eid("s6"),
      ts: "23:05",
      run: {
        id: "eval-prompt-bad",
        trigger: "PROMPT_CHANGED",
        changeSummary: "Rewards Prompt v1.0 → v1.1",
        affectedDomainId: "rewards",
      },
      selectedSuites: promptChangeSuites,
      totalCases: TOTAL_PROMPT_EVAL_CASES,
    },
    {
      type: "CALLOUT_SET",
      id: eid("s6"),
      ts: "23:05",
      callout: {
        title: "Change detected",
        body: "PROMPT_CHANGED · Rewards v1.0 → v1.1 · fingerprint 8ab1 → 91fd",
      },
    },
  ],
};

const step7: DemoStep = {
  id: "step_7_eval_failure",
  number: 7,
  title: "Eval failure",
  concept: "The platform selects relevant tests rather than relying on the domain team to identify blast radius.",
  explanation:
    "The cross-domain Rewards calculation expected 300 points and observed 200. Release status is REGRESSION DETECTED because the bad prompt used the grocery multiplier.",
  presenterNote:
    "Open the eval panel. Call out expected vs actual, then the governance signal — not a dashboard of 10,000 tests.",
  events: [
    ...promptEvalCasesFail.map((result) => ({
      type: (result.passed ? "EVAL_CASE_PASSED" : "EVAL_CASE_FAILED") as
        | "EVAL_CASE_PASSED"
        | "EVAL_CASE_FAILED",
      id: eid("s7"),
      ts: "23:05",
      runId: "eval-prompt-bad",
      result,
    })),
    {
      type: "EVAL_COMPLETED",
      id: eid("s7"),
      ts: "23:05",
      runId: "eval-prompt-bad",
      verdict: "REGRESSION_DETECTED",
      passedCount: 17,
      failedCount: 1,
    },
    ...auditorPipeline({
      prefix: "s7",
      ts: "23:05",
      runId: "audit-rewards-v11",
      subject: "Rewards v1.1 prompt change",
      trigger: "PROMPT_CHANGED",
      domainId: "rewards",
      evalRunId: "eval-prompt-bad",
      manifestHash: BUNDLE_HASH.rewardsV11,
      checks: manifestAuditorChecks({
        domainName: "Rewards",
        bundleHash: BUNDLE_HASH.rewardsV11,
        publishedSkills: rewardsSkillsV1.map((skill) => skill.id),
        publishedTools: rewardsToolsV1.map((tool) => tool.name),
        reachableSkills: rewardsSkillsV1.map((skill) => skill.id),
        reachableTools: rewardsToolsV1.map((tool) => tool.name),
        requiredSuites: promptChangeSuites.map((suite) => suite.suiteId),
        selectedSuites: promptChangeSuites.map((suite) => suite.suiteId),
        evalVerdict: "REGRESSION_DETECTED",
      }),
    }),
    {
      type: "CALLOUT_SET",
      id: eid("s7"),
      ts: "23:05",
      callout: {
        title: "Auditor withheld attestation",
        body: "Evals ran against the new manifest, but the cross-domain journey failed (300 vs 200). The auditor will not attest v1.1.",
      },
    },
  ],
};

const step8: DemoStep = {
  id: "step_8_prompt_fixed",
  number: 8,
  title: "Prompt fixed",
  concept: "The same detection loop certifies a repair without a central code change.",
  explanation:
    "Rewards restored a corrected prompt (91fd → c3e4, v1.1 → v1.2). Targeted evals re-ran and all 18 cases passed.",
  presenterNote:
    "Contrast step 7 and step 8. Same suites, same journey, different prompt file owned by Rewards.",
  events: [
    {
      type: "PROMPT_CHANGED",
      id: eid("s8"),
      ts: "23:06",
      domainId: "rewards",
      fromHash: PROMPT_HASH.bad,
      toHash: PROMPT_HASH.goodV2,
      fromVersion: "1.1",
      toVersion: "1.2",
    },
    {
      type: "EVAL_STARTED",
      id: eid("s8"),
      ts: "23:06",
      run: {
        id: "eval-prompt-good-v2",
        trigger: "PROMPT_CHANGED",
        changeSummary: "Rewards Prompt v1.1 → v1.2",
        affectedDomainId: "rewards",
      },
      selectedSuites: promptChangeSuites,
      totalCases: TOTAL_PROMPT_EVAL_CASES,
    },
    ...promptEvalCasesPass.map((result) => ({
      type: "EVAL_CASE_PASSED" as const,
      id: eid("s8"),
      ts: "23:06",
      runId: "eval-prompt-good-v2",
      result,
    })),
    {
      type: "EVAL_COMPLETED",
      id: eid("s8"),
      ts: "23:06",
      runId: "eval-prompt-good-v2",
      verdict: "PASS",
      passedCount: 18,
      failedCount: 0,
    },
    ...auditorPipeline({
      prefix: "s8",
      ts: "23:06",
      runId: "audit-rewards-v12",
      subject: "Rewards v1.2 prompt repair",
      trigger: "PROMPT_CHANGED",
      domainId: "rewards",
      evalRunId: "eval-prompt-good-v2",
      manifestHash: BUNDLE_HASH.rewardsV12,
      checks: manifestAuditorChecks({
        domainName: "Rewards",
        bundleHash: BUNDLE_HASH.rewardsV12,
        publishedSkills: rewardsSkillsV1.map((skill) => skill.id),
        publishedTools: rewardsToolsV1.map((tool) => tool.name),
        reachableSkills: rewardsSkillsV1.map((skill) => skill.id),
        reachableTools: rewardsToolsV1.map((tool) => tool.name),
        requiredSuites: promptChangeSuites.map((suite) => suite.suiteId),
        selectedSuites: promptChangeSuites.map((suite) => suite.suiteId),
        evalVerdict: "PASS",
      }),
    }),
    {
      type: "CALLOUT_SET",
      id: eid("s8"),
      ts: "23:06",
      callout: {
        title: "Auditor attested v1.2",
        body: "18 / 18 passed on the repaired manifest. The independent auditor attested bundle m-rew-12.",
      },
    },
  ],
};

const step9: DemoStep = {
  id: "step_9_tool_added",
  number: 9,
  title: "New tool added",
  concept: "Domain tool registries expand without editing central source.",
  explanation:
    "Rewards registered get_expiring_points. The tool inventory updated, and tool-selection plus Rewards domain tests were selected automatically.",
  presenterNote:
    "This is the live-edit story in miniature: add a Python tool, restart only Rewards, central notices.",
  events: [
    {
      type: "TOOL_ADDED",
      id: eid("s9"),
      ts: "23:07",
      domainId: "rewards",
      tool: expiringPointsTool,
    },
    {
      type: "EVAL_STARTED",
      id: eid("s9"),
      ts: "23:07",
      run: {
        id: "eval-tool-added",
        trigger: "TOOL_ADDED",
        changeSummary: "Rewards added get_expiring_points",
        affectedDomainId: "rewards",
      },
      selectedSuites: toolAddedSuites,
      totalCases: TOTAL_TOOL_EVAL_CASES,
    },
    ...toolEvalCases.map((result) => ({
      type: "EVAL_CASE_PASSED" as const,
      id: eid("s9"),
      ts: "23:07",
      runId: "eval-tool-added",
      result,
    })),
    {
      type: "EVAL_COMPLETED",
      id: eid("s9"),
      ts: "23:07",
      runId: "eval-tool-added",
      verdict: "PASS",
      passedCount: TOTAL_TOOL_EVAL_CASES,
      failedCount: 0,
    },
    ...auditorPipeline({
      prefix: "s9",
      ts: "23:07",
      runId: "audit-rewards-tool",
      subject: "Rewards tool surface + get_expiring_points",
      trigger: "TOOL_ADDED",
      domainId: "rewards",
      evalRunId: "eval-tool-added",
      manifestHash: BUNDLE_HASH.rewardsV12,
      checks: manifestAuditorChecks({
        domainName: "Rewards",
        bundleHash: BUNDLE_HASH.rewardsV12,
        publishedSkills: rewardsSkillsV1.map((skill) => skill.id),
        publishedTools: [...rewardsToolsV1, expiringPointsTool].map((tool) => tool.name),
        reachableSkills: rewardsSkillsV1.map((skill) => skill.id),
        reachableTools: [...rewardsToolsV1, expiringPointsTool].map((tool) => tool.name),
        requiredSuites: toolAddedSuites.map((suite) => suite.suiteId),
        selectedSuites: toolAddedSuites.map((suite) => suite.suiteId),
        evalVerdict: "PASS",
      }),
    }),
    {
      type: "CALLOUT_SET",
      id: eid("s9"),
      ts: "23:07",
      callout: {
        title: "New tool attested",
        body: "get_expiring_points is in the bundle and is the only new reachable tool. Auditor attested the closed world.",
      },
    },
  ],
};

const step10: DemoStep = {
  id: "step_10_skill_added",
  number: 10,
  title: "New skill / capability added",
  concept: "A domain independently introduced new customer capability.",
  explanation:
    "Before discovery, “When do my points expire?” is unsupported. After Rewards adds the expiring_points skill, the same question routes Rewards → expiring_points → get_expiring_points.",
  presenterNote:
    "Show the unsupported answer first, then the new skill landing, then the successful trace. That before/after is the federated delivery punchline.",
  exampleQuery: EXPIRY_QUERY,
  events: [
    chat("23:08", "m-s10-user-a", "user", EXPIRY_QUERY),
    chat(
      "23:08",
      "m-s10-asst-a",
      "assistant",
      NO_CAPABILITY_ANSWER,
    ),
    {
      type: "SKILL_ADDED",
      id: eid("s10"),
      ts: "23:08",
      domainId: "rewards",
      skill: expiringPointsSkill,
    },
    ...evalPipeline({
      prefix: "s10",
      ts: "23:08",
      runId: "eval-skill-added",
      trigger: "SKILL_ADDED",
      changeSummary: "Rewards added skill expiring_points",
      domainId: "rewards",
      suites: skillAddedSuites,
      cases: skillOnboardingCases,
    }),
    ...auditorPipeline({
      prefix: "s10",
      ts: "23:08",
      runId: "audit-rewards-skill",
      subject: "Rewards capability expiring_points",
      trigger: "SKILL_ADDED",
      domainId: "rewards",
      evalRunId: "eval-skill-added",
      manifestHash: BUNDLE_HASH.rewardsV12,
      checks: manifestAuditorChecks({
        domainName: "Rewards",
        bundleHash: BUNDLE_HASH.rewardsV12,
        publishedSkills: [...rewardsSkillsV1, expiringPointsSkill].map((skill) => skill.id),
        publishedTools: [...rewardsToolsV1, expiringPointsTool].map((tool) => tool.name),
        reachableSkills: [...rewardsSkillsV1, expiringPointsSkill].map((skill) => skill.id),
        reachableTools: [...rewardsToolsV1, expiringPointsTool].map((tool) => tool.name),
        requiredSuites: skillAddedSuites.map((suite) => suite.suiteId),
        selectedSuites: skillAddedSuites.map((suite) => suite.suiteId),
        evalVerdict: "PASS",
      }),
    }),
    chat("23:08", "m-s10-user-b", "user", EXPIRY_QUERY),
    {
      type: "TRACE_STARTED",
      id: eid("s10"),
      ts: "23:08",
      traceId: "tr-s10",
      query: EXPIRY_QUERY,
    },
    {
      type: "LLM_CALLED",
      id: eid("s10"),
      ts: "23:08",
      traceId: "tr-s10",
      span: span({
        id: "tr-s10-planner",
        kind: "planner",
        label: "Central planner",
        startMs: 0,
        durationMs: 50,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s10"),
      ts: "23:08",
      traceId: "tr-s10",
      span: span({
        id: "tr-s10-rew",
        parentId: "tr-s10-planner",
        kind: "delegation",
        label: "Rewards · expiring_points",
        domainId: "rewards",
        startMs: 54,
        durationMs: 95,
      }),
    },
    {
      type: "TOOL_CALLED",
      id: eid("s10"),
      ts: "23:08",
      traceId: "tr-s10",
      span: span({
        id: "tr-s10-tool",
        parentId: "tr-s10-rew",
        kind: "tool",
        label: "get_expiring_points",
        domainId: "rewards",
        toolName: "get_expiring_points",
        startMs: 90,
        durationMs: 16,
      }),
    },
    {
      type: "TRACE_COMPLETED",
      id: eid("s10"),
      ts: "23:08",
      traceId: "tr-s10",
      answer: EXPIRY_ANSWER,
      durationMs: 160,
    },
    chat("23:08", "m-s10-asst-b", "assistant", EXPIRY_ANSWER),
    {
      type: "CALLOUT_SET",
      id: eid("s10"),
      ts: "23:08",
      callout: {
        title: "New customer capability",
        body: "When do my points expire? → Rewards → expiring_points → get_expiring_points",
      },
    },
  ],
};

const step11: DemoStep = {
  id: "step_11_domain_failure",
  number: 11,
  title: "Domain failure",
  concept: "Failure isolation: one domain down does not take the platform or sibling domains with it.",
  explanation:
    "Rewards is unavailable. Transactions-only requests still succeed. Cross-domain Rewards journeys degrade instead of failing the whole system.",
  presenterNote:
    "Run the transactions-only question, then the mixed journey. Healthy vs degraded is the visual.",
  exampleQuery: TRANSACTIONS_ONLY_QUERY,
  events: [
    {
      type: "DOMAIN_OFFLINE",
      id: eid("s11"),
      ts: "23:09",
      domainId: "rewards",
      reason: "Rewards process stopped",
    },
    chat("23:09", "m-s11-user-a", "user", TRANSACTIONS_ONLY_QUERY),
    {
      type: "TRACE_STARTED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11a",
      query: TRANSACTIONS_ONLY_QUERY,
    },
    {
      type: "LLM_CALLED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11a",
      span: span({
        id: "tr-s11a-planner",
        kind: "planner",
        label: "Central planner",
        startMs: 0,
        durationMs: 40,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11a",
      span: span({
        id: "tr-s11a-txn",
        parentId: "tr-s11a-planner",
        kind: "delegation",
        label: "Transactions agent",
        domainId: "transactions",
        startMs: 44,
        durationMs: 80,
      }),
    },
    {
      type: "TOOL_CALLED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11a",
      span: span({
        id: "tr-s11a-tool",
        parentId: "tr-s11a-txn",
        kind: "tool",
        label: "get_recent_transactions",
        domainId: "transactions",
        toolName: "get_recent_transactions",
        startMs: 70,
        durationMs: 20,
      }),
    },
    {
      type: "TRACE_COMPLETED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11a",
      answer: TRANSACTIONS_ONLY_ANSWER,
      durationMs: 130,
    },
    chat("23:09", "m-s11-asst-a", "assistant", TRANSACTIONS_ONLY_ANSWER),
    chat("23:09", "m-s11-user-b", "user", CROSS_DOMAIN_QUERY),
    {
      type: "TRACE_STARTED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11b",
      query: CROSS_DOMAIN_QUERY,
    },
    {
      type: "LLM_CALLED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11b",
      span: span({
        id: "tr-s11b-planner",
        kind: "planner",
        label: "Central planner",
        startMs: 0,
        durationMs: 46,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11b",
      span: span({
        id: "tr-s11b-txn",
        parentId: "tr-s11b-planner",
        kind: "delegation",
        label: "Transactions agent",
        domainId: "transactions",
        startMs: 50,
        durationMs: 72,
      }),
    },
    {
      type: "TOOL_CALLED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11b",
      span: span({
        id: "tr-s11b-tool",
        parentId: "tr-s11b-txn",
        kind: "tool",
        label: "get_transaction_by_id",
        domainId: "transactions",
        toolName: "get_transaction_by_id",
        startMs: 78,
        durationMs: 18,
      }),
    },
    {
      type: "AGENT_DELEGATED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11b",
      span: span({
        id: "tr-s11b-rew",
        parentId: "tr-s11b-planner",
        kind: "delegation",
        label: "Rewards agent",
        domainId: "rewards",
        startMs: 130,
        durationMs: 12,
        status: "error",
      }),
    },
    {
      type: "TRACE_COMPLETED",
      id: eid("s11"),
      ts: "23:09",
      traceId: "tr-s11b",
      answer: DEGRADED_CROSS_DOMAIN_ANSWER,
      durationMs: 150,
      status: "degraded",
    },
    chat("23:09", "m-s11-asst-b", "assistant", DEGRADED_CROSS_DOMAIN_ANSWER),
    {
      type: "CALLOUT_SET",
      id: eid("s11"),
      ts: "23:09",
      callout: {
        title: "Failure isolation",
        body: "Rewards UNAVAILABLE · Transactions HEALTHY · mixed journeys degrade, they do not cascade.",
      },
    },
  ],
};

const step12: DemoStep = {
  id: "step_12_summary",
  number: 12,
  title: "Architecture summary",
  concept:
    "Independent domains + central orchestration + discovery + targeted evals + independent auditor + closed-world reachability + observability + failure isolation.",
  explanation:
    "The platform stayed stable while independently developed domain agents appeared. Central evaluated each change, and a non-LLM auditor attested that published bundles were the only reachable surface.",
  presenterNote:
    "Read the eight principles off the recap, then offer to jump back to any step with the number keys or ?step=.",
  events: [
    {
      type: "DOMAIN_DISCOVERED",
      id: eid("s12"),
      ts: "23:10",
      domain: {
        ...rewardsDomainV1(),
        version: "1.2",
        promptVersion: "1.2",
        promptHash: PROMPT_HASH.goodV2,
        bundleHash: BUNDLE_HASH.rewardsV12,
        tools: [...rewardsDomainV1().tools, expiringPointsTool],
        skills: [...rewardsDomainV1().skills, expiringPointsSkill],
      },
    },
    {
      type: "CALLOUT_SET",
      id: eid("s12"),
      ts: "23:10",
      callout: {
        title: "Federated operating model",
        body: "Centralize orchestration, evals, and observability. Federate domain intelligence. Independently audit the published manifest.",
      },
    },
  ],
};

export const DEMO_STEPS: DemoStep[] = [
  step1,
  step2,
  step3,
  step4,
  step5,
  step6,
  step7,
  step8,
  step9,
  step10,
  step11,
  step12,
];

export const DEMO_STEP_COUNT = DEMO_STEPS.length;
