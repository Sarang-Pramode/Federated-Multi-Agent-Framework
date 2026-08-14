import type { DomainId, DomainState, SystemState } from "@/lib/types";

function offlineDomain(
  id: DomainId,
  name: string,
): DomainState {
  return {
    id,
    name,
    version: "—",
    status: "offline",
    promptVersion: "—",
    promptHash: "—",
    skills: [],
    tools: [],
    modelProvider: "—",
    modelName: "—",
    protocolInterface: "A2A v1.0 / JSON-RPC",
    bundleHash: "—",
    latestEvalStatus: "none",
  };
}

export function createInitialState(): SystemState {
  return {
    central: {
      name: "Central Platform",
      status: "active",
      modelProvider: "openai",
      modelName: "gpt-4.1-mini",
    },
    domains: {
      rewards: offlineDomain("rewards", "Rewards"),
      transactions: offlineDomain("transactions", "Transactions"),
    },
    changes: [],
    traces: [],
    evalRuns: [],
    auditor: {
      status: "idle",
      runs: [],
    },
    customerMessages: [],
    releaseStatus: "stable",
  };
}
