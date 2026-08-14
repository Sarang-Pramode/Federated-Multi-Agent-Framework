"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useDemoController, type DemoController } from "@/hooks/use-demo-controller";

const PlatformContext = createContext<DemoController | null>(null);

export function PlatformProvider({ children }: { children: ReactNode }) {
  const controller = useDemoController();
  return (
    <PlatformContext.Provider value={controller}>
      {children}
    </PlatformContext.Provider>
  );
}

export function usePlatform(): DemoController {
  const value = useContext(PlatformContext);
  if (!value) {
    throw new Error("usePlatform must be used within PlatformProvider");
  }
  return value;
}
