import type { PlatformEvent } from "@/lib/events";

export type EventExplanation = {
  technical: string;
  explanation: string;
};

function domainLabel(id: string): string {
  if (id === "rewards") return "Rewards";
  if (id === "transactions") return "Transactions";
  return id;
}

export function explainEvent(event: PlatformEvent): EventExplanation {
  switch (event.type) {
    case "DOMAIN_DISCOVERED":
      return {
        technical: `Agent Card received for ${event.domain.name} ${event.domain.version}; ${event.domain.skills.length} skills, ${event.domain.tools.length} tools.`,
        explanation: `${event.domain.name} independently came online. The central platform discovered it and expanded the capability inventory without a central code change.`,
      };
    case "DOMAIN_OFFLINE":
      return {
        technical: `${domainLabel(event.domainId)} heartbeat lost${event.reason ? `: ${event.reason}` : ""}.`,
        explanation: `A domain failure is isolated. Central orchestration stays up, and remaining healthy domains continue to serve their own requests.`,
      };
    case "PROMPT_CHANGED":
      return {
        technical: `${domainLabel(event.domainId)} prompt hash changed from ${event.fromHash} → ${event.toHash} (${event.fromVersion} → ${event.toVersion}).`,
        explanation: `${domainLabel(event.domainId)} independently changed its instructions. The central platform detected the change without a manual notification and can select the tests that could be affected.`,
      };
    case "TOOL_ADDED":
      return {
        technical: `Tool registry now includes ${event.tool.name} (schema ${event.tool.schemaHash}) on ${domainLabel(event.domainId)}.`,
        explanation: `A domain added a tool on its own. Central did not ship new business logic — it only observed the updated tool surface.`,
      };
    case "TOOL_REMOVED":
      return {
        technical: `Tool ${event.tool.name} removed from ${domainLabel(event.domainId)}.`,
        explanation: `The domain contracted its tool surface. Central routing will no longer offer that tool.`,
      };
    case "TOOL_SCHEMA_CHANGED":
      return {
        technical: `${event.toolName} schema hash ${event.fromHash} → ${event.toHash}.`,
        explanation: `A tool contract changed. That is a blast-radius signal for tool-selection and journey evals, not a silent schema drift.`,
      };
    case "SKILL_ADDED":
      return {
        technical: `Skill ${event.skill.id} v${event.skill.version} registered on ${domainLabel(event.domainId)}.`,
        explanation: `A domain independently introduced a new customer capability. Discovery makes it visible to the orchestrator.`,
      };
    case "SKILL_REMOVED":
      return {
        technical: `Skill ${event.skill.id} removed from ${domainLabel(event.domainId)}.`,
        explanation: `The domain withdrew a capability. Central inventory shrinks to match reality.`,
      };
    case "EVAL_STARTED":
      return {
        technical: `Eval run ${event.run.id} selected ${event.selectedSuites.map((suite) => suite.suiteId).join(", ")}.`,
        explanation: `Change detection selected a targeted suite instead of asking the domain team to guess the blast radius.`,
      };
    case "EVAL_CASE_PASSED":
      return {
        technical: `${event.result.suiteId}/${event.result.name}: expected ${event.result.expected}, actual ${event.result.actual}.`,
        explanation: `This case still matches ground truth after the change.`,
      };
    case "EVAL_CASE_FAILED":
      return {
        technical: `${event.result.suiteId}/${event.result.name}: expected ${event.result.expected}, actual ${event.result.actual}.`,
        explanation: `A targeted test caught a regression the domain change introduced. That is the governance signal.`,
      };
    case "EVAL_COMPLETED":
      return {
        technical: `Eval ${event.runId} verdict ${event.verdict}.`,
        explanation:
          event.verdict === "REGRESSION_DETECTED"
            ? "Release status is blocked until the owning domain restores the expected behavior."
            : "Targeted evals passed. The change is safe to keep in the federated runtime.",
      };
    case "TRACE_STARTED":
      return {
        technical: `Trace ${event.traceId} opened for query: ${event.query}`,
        explanation: `The central planner received a customer request and started a runtime trace.`,
      };
    case "AGENT_DELEGATED":
      return {
        technical: `Delegated via A2A to ${event.span.label} (${event.span.durationMs}ms).`,
        explanation: `Cross-domain work goes through central. Domain agents do not call each other.`,
      };
    case "TOOL_CALLED":
      return {
        technical: `Tool ${event.span.toolName ?? event.span.label} (${event.span.durationMs}ms).`,
        explanation: `The domain executed a tool it owns. Central never contained that business logic.`,
      };
    case "LLM_CALLED":
      return {
        technical: `LLM span ${event.span.label} (${event.span.durationMs}ms).`,
        explanation: `An agent loop reason/act step ran inside the owning graph, not as a one-shot chain.`,
      };
    case "TRACE_COMPLETED":
      return {
        technical: `Trace ${event.traceId} completed in ${event.durationMs}ms.`,
        explanation:
          event.status === "degraded"
            ? "The planner returned a degraded answer because a required domain was unavailable."
            : "The orchestrator composed a final answer from domain results.",
      };
    case "CHAT_MESSAGE":
      return {
        technical: `${event.message.role}: ${event.message.content.slice(0, 80)}`,
        explanation:
          event.message.role === "user"
            ? "A customer request entered the central experience."
            : "The platform returned an answer based on currently discovered capabilities.",
      };
    case "CALLOUT_SET":
      return {
        technical: event.callout?.title ?? "Callout cleared",
        explanation: event.callout?.body ?? "Architecture callout dismissed.",
      };
    case "AUDITOR_STARTED":
      return {
        technical: `Independent auditor opened run ${event.runId} against manifest ${event.manifestHash}. Method: deterministic hash and set comparison — no LLM.`,
        explanation: `A third-party auditor, not the domain team and not the orchestrator, is checking that the published bundle is the only surface central can reach, and that the right evals ran against that exact manifest.`,
      };
    case "AUDITOR_CHECK_PASSED":
      return {
        technical: `${event.check.name}: expected ${event.check.expected}, actual ${event.check.actual} (${event.check.method}).`,
        explanation: event.check.detail,
      };
    case "AUDITOR_CHECK_FAILED":
      return {
        technical: `${event.check.name} failed: expected ${event.check.expected}, actual ${event.check.actual}.`,
        explanation: event.check.detail,
      };
    case "AUDITOR_COMPLETED":
      return {
        technical: `Auditor verdict ${event.verdict}.`,
        explanation:
          event.verdict === "ATTESTED"
            ? "The auditor attested that the reachable inventory matches the published bundle and that required evals executed against that manifest."
            : "The auditor withheld attestation. Central saw a change, but the control checks did not all pass.",
      };
    default: {
      const _exhaustive: never = event;
      return _exhaustive;
    }
  }
}

export function explainChangeSummary(event: PlatformEvent): string {
  return explainEvent(event).technical;
}
