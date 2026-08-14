"use client";

import { ArchitectureCanvas } from "@/components/architecture/architecture-canvas";
import { CustomerChat } from "@/components/chat/customer-chat";
import { SystemStatePanel } from "@/components/system/system-state-panel";
import { ActivityTabs } from "@/components/activity/activity-tabs";
import { AppHeader } from "@/components/layout/app-header";
import { PresenterFooter } from "@/components/layout/presenter-footer";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useKeyboardNav } from "@/hooks/use-keyboard-nav";
import { usePlatform } from "@/providers/platform-provider";

function LiveBanner() {
  const { liveStatus, mode } = usePlatform();
  if (liveStatus !== "unavailable") return null;
  return (
    <Alert className="mx-4 mt-3 border-status-change/40 bg-status-change/10">
      <AlertTitle>Live backend not connected — Phase 2</AlertTitle>
      <AlertDescription>
        {mode === "demo"
          ? "Guided Demo Mode is still available for the presentation. Connect Central at localhost:8000 to use Live Mode."
          : "Could not reach the central event stream. Returning to Guided Demo Mode."}
      </AlertDescription>
    </Alert>
  );
}

function KeyboardBinder() {
  useKeyboardNav();
  return null;
}

export function DemoShell() {
  return (
    <div className="flex h-screen flex-col bg-background">
      <KeyboardBinder />
      <AppHeader />
      <LiveBanner />
      <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-4 lg:grid-cols-[minmax(300px,0.85fr)_minmax(0,1.15fr)_minmax(240px,0.7fr)] lg:grid-rows-[minmax(220px,0.7fr)_minmax(0,1.3fr)]">
        <div className="h-full min-h-[520px] min-w-0 lg:row-span-2 lg:min-h-0">
          <ArchitectureCanvas />
        </div>
        <div className="h-full min-h-[220px] min-w-0">
          <CustomerChat />
        </div>
        <div className="h-full min-h-[220px] min-w-0">
          <SystemStatePanel />
        </div>
        <div className="h-full min-h-[340px] min-w-0 lg:col-span-2">
          <ActivityTabs />
        </div>
      </main>
      <PresenterFooter />
    </div>
  );
}
