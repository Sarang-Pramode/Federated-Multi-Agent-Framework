import { describe, expect, it } from "vitest";
import { DEMO_STEPS } from "@/demo/scenarios";
import { applyEvents, eventsThroughStep } from "@/lib/state/reducer";
import { getLatestEvalRun } from "@/lib/state/selectors";

function stateAt(index: number) {
  return applyEvents(eventsThroughStep(DEMO_STEPS, index));
}

describe("demo reducer replay", () => {
  it("has 12 guided steps", () => {
    expect(DEMO_STEPS).toHaveLength(12);
    expect(DEMO_STEPS.map((step) => step.number)).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    ]);
  });

  it("replays to the same step twice with identical state", () => {
    for (let index = 0; index < DEMO_STEPS.length; index += 1) {
      expect(stateAt(index)).toEqual(stateAt(index));
    }
  });

  it("forward-then-back equals direct replay", () => {
    const direct = stateAt(4);
    const viaLater = applyEvents(eventsThroughStep(DEMO_STEPS, 6));
    const backToFive = applyEvents(eventsThroughStep(DEMO_STEPS, 4));
    expect(backToFive).toEqual(direct);
    expect(viaLater.evalRuns.length).toBeGreaterThan(direct.evalRuns.length);
  });

  it("step 1 has no domain capabilities and a degraded points answer", () => {
    const state = stateAt(0);
    expect(state.domains.rewards.status).toBe("offline");
    expect(state.domains.transactions.status).toBe("offline");
    expect(state.domains.rewards.skills).toHaveLength(0);
    expect(state.customerMessages.at(-1)?.content).toContain(
      "No available domain capability",
    );
  });

  it("step 2 discovers Rewards, runs onboarding evals, and auditor attests", () => {
    const state = stateAt(1);
    expect(state.domains.rewards.status).toBe("active");
    expect(state.domains.rewards.skills.map((skill) => skill.id)).toEqual([
      "check_points_balance",
      "explain_rewards_program",
      "missing_points",
    ]);
    expect(state.domains.rewards.tools.map((tool) => tool.name)).toEqual([
      "get_points_balance",
      "calculate_rewards",
    ]);
    expect(getLatestEvalRun(state)?.trigger).toBe("AGENT_ADDED");
    expect(getLatestEvalRun(state)?.verdict).toBe("PASS");
    expect(state.auditor.status).toBe("ATTESTED");
  });

  it("step 3 answers the points question with 12,500", () => {
    const state = stateAt(2);
    expect(state.customerMessages.at(-1)?.content).toContain("12,500");
    const trace = state.traces.at(-1);
    expect(trace?.spans.some((span) => span.toolName === "get_points_balance")).toBe(
      true,
    );
  });

  it("step 5 fans out to both domains and returns 300 points", () => {
    const state = stateAt(4);
    const trace = state.traces.find((item) => item.id === "tr-s5");
    expect(trace?.spans.some((span) => span.domainId === "rewards")).toBe(true);
    expect(trace?.spans.some((span) => span.domainId === "transactions")).toBe(
      true,
    );
    expect(trace?.spans.some((span) => span.toolName === "get_transaction_by_id")).toBe(
      true,
    );
    expect(trace?.spans.some((span) => span.toolName === "calculate_rewards")).toBe(
      true,
    );
    expect(state.customerMessages.at(-1)?.content).toContain("300 points");
  });

  it("step 7 records a cross-domain regression 17/18 and auditor withholds", () => {
    const state = stateAt(6);
    expect(state.releaseStatus).toBe("REGRESSION_DETECTED");
    const run = getLatestEvalRun(state);
    expect(run?.passedCount).toBe(17);
    expect(run?.failedCount).toBe(1);
    expect(run?.results.find((result) => !result.passed)?.actual).toBe(
      "200 points",
    );
    expect(run?.results.find((result) => !result.passed)?.expected).toBe(
      "300 points",
    );
    expect(state.auditor.status).toBe("WITHHELD");
  });

  it("step 8 clears the regression", () => {
    const state = stateAt(7);
    expect(state.releaseStatus).toBe("passing");
    expect(getLatestEvalRun(state)?.verdict).toBe("PASS");
    expect(state.domains.rewards.promptHash).toBe("c3e4");
    expect(state.auditor.status).toBe("ATTESTED");
  });

  it("step 10 adds expiring_points and answers expiry", () => {
    const state = stateAt(9);
    expect(
      state.domains.rewards.skills.some((skill) => skill.id === "expiring_points"),
    ).toBe(true);
    expect(
      state.domains.rewards.tools.some((tool) => tool.name === "get_expiring_points"),
    ).toBe(true);
    expect(state.customerMessages.at(-1)?.content).toContain("expire");
  });

  it("step 11 isolates Rewards failure while Transactions stays up", () => {
    const state = stateAt(10);
    expect(state.domains.rewards.status).toBe("unavailable");
    expect(state.domains.transactions.status).toBe("active");
    expect(
      state.customerMessages.some((message) =>
        message.content.includes("T1001 at Demo Bistro"),
      ),
    ).toBe(true);
    expect(state.traces.find((trace) => trace.id === "tr-s11b")?.status).toBe(
      "degraded",
    );
  });
});
