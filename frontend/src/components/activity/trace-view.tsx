"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePlatform } from "@/providers/platform-provider";
import { getActiveTrace } from "@/lib/state/selectors";
import type { SpanSnapshot } from "@/lib/types";
import { cn } from "@/lib/utils";

function depthOf(span: SpanSnapshot, byId: Map<string, SpanSnapshot>): number {
  let depth = 0;
  let current: SpanSnapshot | undefined = span;
  const seen = new Set<string>();
  while (current?.parentId && !seen.has(current.id)) {
    seen.add(current.id);
    current = byId.get(current.parentId);
    depth += 1;
  }
  return depth;
}

const kindLabel: Record<SpanSnapshot["kind"], string> = {
  planner: "planner",
  delegation: "agent",
  agent_loop: "loop",
  tool: "tool",
  llm: "llm",
  final: "final",
};

export function TraceView() {
  const { state } = usePlatform();
  const trace = getActiveTrace(state);

  if (!trace) {
    return (
      <EmptyState
        title="No runtime trace"
        description="Customer requests will show planner, delegation, and tool spans here."
      />
    );
  }

  const byId = new Map(trace.spans.map((span) => [span.id, span]));

  return (
    <ScrollArea className="h-full">
      <div className="pr-2">
        <div className="mb-2 flex items-baseline justify-between gap-2">
          <p className="truncate text-sm font-medium">{trace.query}</p>
          <p className="shrink-0 font-mono text-[11px] text-muted-foreground">
            {trace.durationMs ? `${trace.durationMs}ms total` : "running"}
            {trace.status === "degraded" ? " · degraded" : ""}
          </p>
        </div>
        <ol className="font-mono text-sm">
          <li className="text-muted-foreground">request</li>
          {trace.spans.map((span) => {
            const depth = depthOf(span, byId) + 1;
            return (
              <li
                key={span.id}
                className={cn(
                  "flex items-center justify-between gap-2 py-0.5",
                  span.status === "error" && "text-status-fail-foreground",
                )}
                style={{ paddingLeft: depth * 14 }}
              >
                <span>
                  <span className="text-muted-foreground">└ </span>
                  <span className="text-[10px] uppercase tracking-wide text-primary">
                    {kindLabel[span.kind]}
                  </span>{" "}
                  {span.label}
                </span>
                <span className="text-muted-foreground">{span.durationMs}ms</span>
              </li>
            );
          })}
        </ol>
        {trace.answer ? (
          <p className="mt-3 rounded-md border border-border bg-muted/40 px-2 py-1.5 text-xs leading-relaxed">
            {trace.answer}
          </p>
        ) : null}
      </div>
    </ScrollArea>
  );
}
