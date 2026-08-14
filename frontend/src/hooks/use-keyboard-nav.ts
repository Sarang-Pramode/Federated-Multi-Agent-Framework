"use client";

import { useEffect } from "react";
import { usePlatform } from "@/providers/platform-provider";

export function useKeyboardNav() {
  const { next, back, reset, goToStep, mode } =
    usePlatform();

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }

      if (event.key === "ArrowRight" || event.key === " ") {
        event.preventDefault();
        next();
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        back();
        return;
      }
      if (event.key === "r" && event.metaKey === false && event.ctrlKey === false) {
        if (mode === "demo") {
          event.preventDefault();
          reset();
        }
        return;
      }
      if (/^[1-9]$/.test(event.key) || event.key === "0") {
        const index = event.key === "0" ? 9 : Number(event.key) - 1;
        if (index < 12) {
          event.preventDefault();
          goToStep(index);
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [next, back, reset, goToStep, mode]);
}
