"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { DEMO_STEPS } from "@/demo/scenarios";
import type { PlatformEvent } from "@/lib/events";
import { createInitialState } from "@/lib/state/initial-state";
import { applyEvent, applyEvents, eventsThroughStep } from "@/lib/state/reducer";
import type { DemoMode, SystemState } from "@/lib/types";
import { LiveTransport } from "@/lib/transport/live-transport";
import { MockTransport } from "@/lib/transport/mock-transport";
import type { LiveConnectionStatus } from "@/lib/transport/types";

const STEP_COUNT = DEMO_STEPS.length;

function parseStepParam(value: string | null): number {
  if (!value) return 0;
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) return 0;
  return Math.min(STEP_COUNT, Math.max(1, parsed)) - 1;
}

export function useDemoController() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const requestedStep = parseStepParam(searchParams.get("step"));

  const [stepIndex, setStepIndex] = useState(requestedStep);
  const [state, setState] = useState<SystemState>(() =>
    applyEvents(eventsThroughStep(DEMO_STEPS, requestedStep)),
  );
  const [mode, setMode] = useState<DemoMode>("demo");
  const [liveStatus, setLiveStatus] = useState<LiveConnectionStatus>("idle");
  const [isAnimating, setIsAnimating] = useState(false);
  const [animate, setAnimate] = useState(false);

  const mockRef = useRef<MockTransport | null>(null);
  const liveRef = useRef<LiveTransport | null>(null);
  const stepRef = useRef(stepIndex);

  stepRef.current = stepIndex;

  const currentStep = DEMO_STEPS[stepIndex];

  const syncUrl = useCallback(
    (index: number) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("step", String(index + 1));
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    const transport = new MockTransport({
      onEvent: (event: PlatformEvent) => {
        setState((current) => applyEvent(current, event));
      },
      onIdle: () => setIsAnimating(false),
    });
    mockRef.current = transport;
    return () => transport.stop();
  }, []);

  const replayTo = useCallback((index: number, withAnimation: boolean) => {
    mockRef.current?.stop();
    const clamped = Math.min(STEP_COUNT - 1, Math.max(0, index));
    setStepIndex(clamped);
    syncUrl(clamped);

    if (withAnimation && clamped > 0) {
      const prefix = eventsThroughStep(DEMO_STEPS, clamped - 1);
      setAnimate(true);
      setState(applyEvents(prefix));
      setIsAnimating(true);
      mockRef.current?.play(DEMO_STEPS[clamped].events);
      return;
    }

    setAnimate(false);
    setIsAnimating(false);
    setState(applyEvents(eventsThroughStep(DEMO_STEPS, clamped)));
  }, [syncUrl]);

  useEffect(() => {
    if (requestedStep !== stepRef.current && !isAnimating) {
      replayTo(requestedStep, false);
    }
  }, [requestedStep, isAnimating, replayTo]);

  const next = useCallback(() => {
    if (mode !== "demo") return;
    if (mockRef.current?.isBusy) {
      mockRef.current.flush();
      return;
    }
    if (stepRef.current >= STEP_COUNT - 1) return;
    replayTo(stepRef.current + 1, true);
  }, [mode, replayTo]);

  const back = useCallback(() => {
    if (mode !== "demo") return;
    if (stepRef.current <= 0) return;
    replayTo(stepRef.current - 1, false);
  }, [mode, replayTo]);

  const reset = useCallback(() => {
    if (mode !== "demo") {
      setState(createInitialState());
      return;
    }
    replayTo(0, false);
  }, [mode, replayTo]);

  const goToStep = useCallback(
    (index: number) => {
      replayTo(index, false);
    },
    [replayTo],
  );

  const switchMode = useCallback((nextMode: DemoMode) => {
    mockRef.current?.stop();
    liveRef.current?.stop();
    setMode(nextMode);

    if (nextMode === "demo") {
      setLiveStatus("idle");
      replayTo(stepRef.current, false);
      return;
    }

    setAnimate(true);
    setState(createInitialState());
    const live = new LiveTransport({
      onEvent: (event) => setState((current) => applyEvent(current, event)),
      onStatus: (status) => {
        setLiveStatus(status);
        if (status === "unavailable") {
          setMode("demo");
          replayTo(stepRef.current, false);
        }
      },
    });
    liveRef.current = live;
    live.start();
  }, [replayTo]);

  useEffect(() => {
    return () => liveRef.current?.stop();
  }, []);

  return useMemo(
    () => ({
      state,
      mode,
      liveStatus,
      isAnimating,
      animate,
      currentStep,
      stepIndex,
      stepCount: STEP_COUNT,
      steps: DEMO_STEPS,
      next,
      back,
      reset,
      goToStep,
      setMode: switchMode,
    }),
    [
      state,
      mode,
      liveStatus,
      isAnimating,
      animate,
      currentStep,
      stepIndex,
      next,
      back,
      reset,
      goToStep,
      switchMode,
    ],
  );
}

export type DemoController = ReturnType<typeof useDemoController>;
