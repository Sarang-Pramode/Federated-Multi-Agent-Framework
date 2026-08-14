"use client";

import { CapabilityList } from "@/components/system/capability-list";
import { ToolList } from "@/components/system/tool-list";
import {
  domainStatusLabel,
  domainStatusTone,
  evalTone,
  StatusBadge,
} from "@/components/common/status-badge";
import type { DomainState } from "@/lib/types";
import { cn } from "@/lib/utils";

export function DomainCard({
  domain,
  isolateHealthy,
  animate,
}: {
  domain: DomainState;
  isolateHealthy: boolean;
  animate: boolean;
}) {
  const dimmed = domain.status === "offline";

  return (
    <article
      className={cn(
        "rounded-lg border border-border bg-background p-3 shadow-xs",
        dimmed && "opacity-70",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold">{domain.name}</h3>
          <p className="font-mono text-[11px] text-muted-foreground">
            {domain.version === "—"
              ? "Not discovered"
              : `v${domain.version} · prompt ${domain.promptVersion} · ${domain.promptHash}`}
          </p>
        </div>
        <StatusBadge tone={domainStatusTone(domain.status)}>
          {domainStatusLabel(domain.status, isolateHealthy)}
        </StatusBadge>
      </div>

      <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
        <div>
          <dt className="text-muted-foreground">Model</dt>
          <dd className="font-mono">
            {domain.modelProvider}/{domain.modelName}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Latest eval</dt>
          <dd>
            <StatusBadge tone={evalTone(domain.latestEvalStatus)}>
              {domain.latestEvalStatus}
            </StatusBadge>
          </dd>
        </div>
        <div className="col-span-2">
          <dt className="text-muted-foreground">Latest change</dt>
          <dd>{domain.latestChange ?? "—"}</dd>
        </div>
      </dl>

      <div className="mt-2 space-y-1.5">
        <p className="text-[11px] font-medium text-muted-foreground">Skills</p>
        <CapabilityList skills={domain.skills} animate={animate} />
        <p className="text-[11px] font-medium text-muted-foreground">Tools</p>
        <ToolList tools={domain.tools} animate={animate} />
      </div>
    </article>
  );
}
