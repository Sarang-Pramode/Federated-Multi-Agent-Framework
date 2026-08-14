"use client";

import { Suspense } from "react";
import { DemoShell } from "@/components/layout/demo-shell";
import { PlatformProvider } from "@/providers/platform-provider";

function DemoFallback() {
  return (
    <div className="flex h-screen items-center justify-center bg-background text-sm text-muted-foreground">
      Loading federated agent demo…
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<DemoFallback />}>
      <PlatformProvider>
        <DemoShell />
      </PlatformProvider>
    </Suspense>
  );
}
