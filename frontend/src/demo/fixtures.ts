import type {
  AuditorCheck,
  DomainSnapshot,
  EvalCaseResult,
  SkillSnapshot,
  SuiteSelection,
  ToolSnapshot,
} from "@/lib/types";

export const PROMPT_HASH = {
  good: "8ab1",
  bad: "91fd",
  goodV2: "c3e4",
} as const;

export const TOOL_HASH = {
  get_points_balance: "t4c1",
  calculate_rewards: "t8d2",
  get_expiring_points: "t2e9",
  get_recent_transactions: "t1a0",
  get_transaction_by_id: "t7b3",
} as const;

export const BUNDLE_HASH = {
  rewardsV1: "m-rew-10",
  rewardsV11: "m-rew-11",
  rewardsV12: "m-rew-12",
  transactionsV1: "m-txn-10",
} as const;

export const CUSTOMER = {
  id: "demo-user",
  points: 12500,
} as const;

export const TRANSACTION = {
  id: "T1001",
  merchant: "Demo Bistro",
  category: "restaurant",
  amount: 100,
  status: "posted",
} as const;

export const REWARD_RULES = {
  restaurant: 3,
  grocery: 2,
  base: 1,
} as const;

export const POINTS_QUERY = "How many points do I have?";
export const CROSS_DOMAIN_QUERY =
  "How many points should my Demo Bistro transaction earn?";
export const EXPIRY_QUERY = "When do my points expire?";
export const TRANSACTIONS_ONLY_QUERY = "Show my latest restaurant transaction.";

export const NO_CAPABILITY_ANSWER =
  "No available domain capability can answer this request.";

export const POINTS_ANSWER = "You have 12,500 points.";
export const CROSS_DOMAIN_ANSWER =
  "Your Demo Bistro purchase of $100 in the restaurant category earns 300 points (3× multiplier).";
export const CROSS_DOMAIN_BAD_ANSWER =
  "Your Demo Bistro purchase earns 200 points.";
export const EXPIRY_ANSWER =
  "1,200 of your points expire on September 30, 2026.";
export const TRANSACTIONS_ONLY_ANSWER =
  "Your latest restaurant transaction is T1001 at Demo Bistro for $100 (posted).";
export const DEGRADED_CROSS_DOMAIN_ANSWER =
  "I found your Demo Bistro transaction (T1001, $100, restaurant), but Rewards is unavailable so I cannot calculate points right now.";

export const rewardsSkillsV1: SkillSnapshot[] = [
  {
    id: "check_points_balance",
    name: "Check points balance",
    description: "Look up the customer's current rewards balance.",
    allowedTools: ["get_points_balance"],
    version: "1.0",
    enabled: true,
  },
  {
    id: "explain_rewards_program",
    name: "Explain rewards program",
    description: "Explain how the rewards program and multipliers work.",
    allowedTools: ["calculate_rewards"],
    version: "1.0",
    enabled: true,
  },
  {
    id: "missing_points",
    name: "Missing points",
    description: "Investigate why expected points may not have posted.",
    allowedTools: ["get_points_balance", "calculate_rewards"],
    version: "1.0",
    enabled: true,
  },
];

export const expiringPointsSkill: SkillSnapshot = {
  id: "expiring_points",
  name: "Expiring points",
  description: "Tell the customer when points will expire.",
  allowedTools: ["get_expiring_points"],
  version: "1.0",
  enabled: true,
};

export const rewardsToolsV1: ToolSnapshot[] = [
  {
    name: "get_points_balance",
    description: "Return the current points balance for a customer.",
    schemaHash: TOOL_HASH.get_points_balance,
  },
  {
    name: "calculate_rewards",
    description: "Calculate points earned for a categorized purchase.",
    schemaHash: TOOL_HASH.calculate_rewards,
  },
];

export const expiringPointsTool: ToolSnapshot = {
  name: "get_expiring_points",
  description: "Return points that will expire and the expiration date.",
  schemaHash: TOOL_HASH.get_expiring_points,
};

export const transactionsSkills: SkillSnapshot[] = [
  {
    id: "recent_transactions",
    name: "Recent transactions",
    description: "List recent posted transactions.",
    allowedTools: ["get_recent_transactions"],
    version: "1.0",
    enabled: true,
  },
  {
    id: "find_transaction",
    name: "Find transaction",
    description: "Look up a transaction by id or merchant.",
    allowedTools: ["get_transaction_by_id"],
    version: "1.0",
    enabled: true,
  },
];

export const transactionsTools: ToolSnapshot[] = [
  {
    name: "get_recent_transactions",
    description: "Return recent transactions for a customer.",
    schemaHash: TOOL_HASH.get_recent_transactions,
  },
  {
    name: "get_transaction_by_id",
    description: "Fetch a single transaction by identifier.",
    schemaHash: TOOL_HASH.get_transaction_by_id,
  },
];

export function rewardsDomainV1(): DomainSnapshot {
  return {
    id: "rewards",
    name: "Rewards",
    version: "1.0",
    status: "active",
    promptVersion: "1.0",
    promptHash: PROMPT_HASH.good,
    skills: rewardsSkillsV1,
    tools: rewardsToolsV1,
    modelProvider: "openai",
    modelName: "gpt-4.1-mini",
    protocolInterface: "A2A v1.0 / JSON-RPC",
    bundleHash: BUNDLE_HASH.rewardsV1,
  };
}

export function transactionsDomainV1(): DomainSnapshot {
  return {
    id: "transactions",
    name: "Transactions",
    version: "1.0",
    status: "active",
    promptVersion: "1.0",
    promptHash: "b2c7",
    skills: transactionsSkills,
    tools: transactionsTools,
    modelProvider: "openai",
    modelName: "gpt-4.1-mini",
    protocolInterface: "A2A v1.0 / JSON-RPC",
    bundleHash: BUNDLE_HASH.transactionsV1,
  };
}

export const promptChangeSuites: SuiteSelection[] = [
  {
    suiteId: "intent",
    suiteName: "Intent classification",
    reason: "Prompt changes can alter how the planner classifies customer intent.",
  },
  {
    suiteId: "rewards_regression",
    suiteName: "Rewards domain regression",
    reason: "The changed prompt belongs to Rewards, so domain-owned cases must re-run.",
  },
  {
    suiteId: "cross_domain",
    suiteName: "Cross-domain journey",
    reason: "Rewards participates in the Demo Bistro points calculation journey.",
  },
  {
    suiteId: "response_judge",
    suiteName: "LLM response judge",
    reason: "Instruction changes can drift factual completeness even when routing stays correct.",
  },
];

export const toolAddedSuites: SuiteSelection[] = [
  {
    suiteId: "tool_selection",
    suiteName: "Tool-selection eval",
    reason: "A new tool changes the action space the Rewards agent can choose from.",
  },
  {
    suiteId: "rewards_regression",
    suiteName: "Rewards domain tests",
    reason: "Existing Rewards cases must still select the original tools when appropriate.",
  },
];

export const skillAddedSuites: SuiteSelection[] = [
  {
    suiteId: "intent",
    suiteName: "Intent / routing eval",
    reason: "A new capability can change which domain and skill the planner selects.",
  },
  {
    suiteId: "capability_smoke",
    suiteName: "Capability smoke test",
    reason: "The new expiring_points skill should answer a previously unsupported question.",
  },
];

export const rewardsOnboardingSuites: SuiteSelection[] = [
  {
    suiteId: "intent",
    suiteName: "Intent / routing eval",
    reason: "A new domain changes which intents central can route. Frozen cases check Rewards vs out-of-scope.",
  },
  {
    suiteId: "rewards_smoke",
    suiteName: "Rewards smoke tests",
    reason: "Central must prove the advertised Rewards skills and tools actually answer known questions.",
  },
];

export const transactionsOnboardingSuites: SuiteSelection[] = [
  {
    suiteId: "intent",
    suiteName: "Intent / routing eval",
    reason: "Transactions coming online adds a new routing target for transaction intents.",
  },
  {
    suiteId: "transactions_smoke",
    suiteName: "Transactions smoke tests",
    reason: "Central must prove advertised transaction tools resolve known lookup cases.",
  },
];

export const skillOnboardingCases: EvalCaseResult[] = [
  pass("s01", "intent", "Expiry question now REWARDS", "REWARDS"),
  pass("s02", "intent", "Balance still REWARDS", "REWARDS"),
  pass("s03", "capability_smoke", "Expiry routes to expiring_points", "expiring_points"),
  pass("s04", "capability_smoke", "Expiry tool get_expiring_points", "get_expiring_points"),
  pass("s05", "capability_smoke", "Expiry answer grounded", "1200 expire 2026-09-30"),
];

function pass(
  id: string,
  suiteId: string,
  name: string,
  expected: string,
  actual = expected,
): EvalCaseResult {
  return { id, suiteId, name, expected, actual, passed: true };
}

function fail(
  id: string,
  suiteId: string,
  name: string,
  expected: string,
  actual: string,
  reason: string,
): EvalCaseResult {
  return { id, suiteId, name, expected, actual, reason, passed: false };
}

export const promptEvalCasesPass: EvalCaseResult[] = [
  pass("c01", "intent", "Small talk", "SMALL_TALK"),
  pass("c02", "intent", "Points balance", "REWARDS"),
  pass("c03", "intent", "Latest restaurant txn", "TRANSACTIONS"),
  pass("c04", "intent", "Restaurant points mix", "MIXED_REWARDS_TRANSACTIONS"),
  pass("c05", "intent", "Book a flight", "OUT_OF_SCOPE"),
  pass("c06", "intent", "Hello greeting", "SMALL_TALK"),
  pass("c07", "intent", "Missing points", "REWARDS"),
  pass("c08", "intent", "Find T1001", "TRANSACTIONS"),
  pass("c09", "rewards_regression", "Balance lookup", "get_points_balance"),
  pass("c10", "rewards_regression", "Program explain", "explain_rewards_program"),
  pass("c11", "rewards_regression", "Balance value", "12500"),
  pass("c12", "rewards_regression", "Restaurant 3x rule", "3"),
  pass(
    "c13",
    "cross_domain",
    "Cross-domain Rewards Calculation",
    "300 points",
    "300 points",
  ),
  pass("c14", "response_judge", "Balance grounded", "pass / 0.92"),
  pass("c15", "response_judge", "Txn lookup grounded", "pass / 0.90"),
  pass("c16", "response_judge", "Out of scope refusal", "pass / 0.88"),
  pass("c17", "response_judge", "Small talk relevant", "pass / 0.86"),
  pass("c18", "response_judge", "Mixed journey complete", "pass / 0.91"),
];

export const promptEvalCasesFail: EvalCaseResult[] = promptEvalCasesPass.map(
  (result) => {
    if (result.id !== "c13") return result;
    return fail(
      "c13",
      "cross_domain",
      "Cross-domain Rewards Calculation",
      "300 points",
      "200 points",
      "Bad prompt applied grocery 2× instead of restaurant 3×.",
    );
  },
);

export const toolEvalCases: EvalCaseResult[] = [
  pass("t01", "tool_selection", "Balance question", "get_points_balance"),
  pass("t02", "tool_selection", "Restaurant earn question", "calculate_rewards"),
  pass("t03", "tool_selection", "Expiry question", "get_expiring_points"),
  pass("t04", "tool_selection", "No extra tool on greeting", "none"),
  pass("t05", "rewards_regression", "Balance still correct", "12500"),
  pass("t06", "rewards_regression", "3× restaurant still correct", "300"),
];

export const rewardsOnboardingCases: EvalCaseResult[] = [
  pass("r01", "intent", "Points balance → REWARDS", "REWARDS"),
  pass("r02", "intent", "Hello → SMALL_TALK", "SMALL_TALK"),
  pass("r03", "intent", "Book a flight → OUT_OF_SCOPE", "OUT_OF_SCOPE"),
  pass("r04", "rewards_smoke", "Balance uses get_points_balance", "get_points_balance"),
  pass("r05", "rewards_smoke", "Balance value 12500", "12500"),
];

export const transactionsOnboardingCases: EvalCaseResult[] = [
  pass("x01", "intent", "Latest restaurant txn → TRANSACTIONS", "TRANSACTIONS"),
  pass("x02", "intent", "Find T1001 → TRANSACTIONS", "TRANSACTIONS"),
  pass("x03", "transactions_smoke", "Lookup uses get_transaction_by_id", "get_transaction_by_id"),
  pass("x04", "transactions_smoke", "T1001 merchant Demo Bistro", "Demo Bistro"),
  pass("x05", "transactions_smoke", "T1001 amount 100", "100"),
];

export const TOTAL_PROMPT_EVAL_CASES = promptEvalCasesPass.length;
export const TOTAL_TOOL_EVAL_CASES = toolEvalCases.length;
export const TOTAL_REWARDS_ONBOARDING_CASES = rewardsOnboardingCases.length;
export const TOTAL_TRANSACTIONS_ONBOARDING_CASES = transactionsOnboardingCases.length;
export const TOTAL_SKILL_ONBOARDING_CASES = skillOnboardingCases.length;

export function manifestAuditorChecks(input: {
  domainName: string;
  bundleHash: string;
  publishedSkills: string[];
  publishedTools: string[];
  reachableSkills: string[];
  reachableTools: string[];
  requiredSuites: string[];
  selectedSuites: string[];
  evalVerdict: "PASS" | "REGRESSION_DETECTED" | "RUNNING";
}): AuditorCheck[] {
  const skillMatch =
    input.publishedSkills.join(",") === input.reachableSkills.join(",");
  const toolMatch =
    input.publishedTools.join(",") === input.reachableTools.join(",");
  const coverage = input.requiredSuites.every((suite) =>
    input.selectedSuites.includes(suite),
  );
  const evalPassed = input.evalVerdict === "PASS";

  return [
    {
      id: "manifest-published",
      name: "Manifest published",
      method: "hash-compare",
      expected: input.bundleHash,
      actual: input.bundleHash,
      passed: true,
      detail: `${input.domainName} published bundle ${input.bundleHash}. The auditor hashes the Agent Card; it does not trust a domain-declared change type.`,
    },
    {
      id: "reachability-closed",
      name: "Closed-world reachability",
      method: "set-compare",
      expected: `skills[${input.publishedSkills.join(", ")}] tools[${input.publishedTools.join(", ")}]`,
      actual: `skills[${input.reachableSkills.join(", ")}] tools[${input.reachableTools.join(", ")}]`,
      passed: skillMatch && toolMatch,
      detail: skillMatch && toolMatch
        ? "Every skill and tool in the bundle is reachable by central, and nothing extra is reachable."
        : "Central can reach a surface that is not identical to the published bundle.",
    },
    {
      id: "eval-coverage",
      name: "Required evals selected",
      method: "rule",
      expected: input.requiredSuites.join(", "),
      actual: input.selectedSuites.join(", "),
      passed: coverage,
      detail: coverage
        ? "Central selected the suites mapped from this change type. Domain teams did not pick the blast radius."
        : "Required suites for this change type were missing from the eval selection.",
    },
    {
      id: "eval-executed",
      name: "Evals executed against this manifest",
      method: "rule",
      expected: "PASS",
      actual: input.evalVerdict,
      passed: evalPassed,
      detail: evalPassed
        ? "Deterministic suites finished against the tested manifest version."
        : "The auditor withholds attestation until the required evals pass on this manifest.",
    },
  ];
}
