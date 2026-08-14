"use client";

import { DomainCard } from "@/components/system/domain-card";
import { StatusBadge } from "@/components/common/status-badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePlatform } from "@/providers/platform-provider";
import { getDomainList } from "@/lib/state/selectors";

export function SystemStatePanel() {
  const { state, animate } = usePlatform();
  const domains = getDomainList(state);
  const isolate = domains.some((domain) => domain.status === "unavailable");

  return (
    <section className="flex h-full min-h-0 flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <h2 className="text-sm font-semibold">System State</h2>
        <StatusBadge tone="healthy">Central Active</StatusBadge>
      </div>
      <ScrollArea className="min-h-0 flex-1 px-3 py-3">
        <div className="space-y-3">
          {domains.map((domain) => (
            <DomainCard
              key={domain.id}
              domain={domain}
              isolateHealthy={isolate && domain.status === "active"}
              animate={animate}
            />
          ))}
        </div>
      </ScrollArea>
    </section>
  );
}
