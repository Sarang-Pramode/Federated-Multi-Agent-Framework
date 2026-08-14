"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChangeFeed } from "@/components/activity/change-feed";
import { EvalPanel } from "@/components/activity/eval-panel";
import { TraceView } from "@/components/activity/trace-view";
import { AuditorPanel } from "@/components/activity/auditor-panel";
import { usePlatform } from "@/providers/platform-provider";

export function ActivityTabs() {
  const { currentStep } = usePlatform();
  const defaultTab =
    currentStep.number === 2 ||
    currentStep.number === 4 ||
    currentStep.number === 6 ||
    currentStep.number === 9 ||
    currentStep.number === 10
      ? "evals"
      : currentStep.number === 7 || currentStep.number === 8
        ? "auditor"
        : currentStep.number === 3 ||
            currentStep.number === 5 ||
            currentStep.number === 11
          ? "trace"
          : "changes";

  return (
    <section className="flex h-full min-h-0 flex-col rounded-xl border border-border bg-card shadow-sm">
      <Tabs key={defaultTab} defaultValue={defaultTab} className="flex min-h-0 flex-1 flex-col">
        <div className="border-b border-border px-3 pt-2">
          <TabsList variant="line" className="w-full justify-start">
            <TabsTrigger value="changes">Change Detection</TabsTrigger>
            <TabsTrigger value="evals">Evaluation</TabsTrigger>
            <TabsTrigger value="auditor">Auditor</TabsTrigger>
            <TabsTrigger value="trace">Trace Timeline</TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="changes" className="min-h-0 flex-1 overflow-hidden px-4 py-4">
          <ChangeFeed />
        </TabsContent>
        <TabsContent value="evals" className="min-h-0 flex-1 overflow-hidden px-4 py-4">
          <EvalPanel />
        </TabsContent>
        <TabsContent value="auditor" className="min-h-0 flex-1 overflow-hidden px-4 py-4">
          <AuditorPanel />
        </TabsContent>
        <TabsContent value="trace" className="min-h-0 flex-1 overflow-hidden px-4 py-4">
          <TraceView />
        </TabsContent>
      </Tabs>
    </section>
  );
}
