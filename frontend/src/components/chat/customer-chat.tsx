"use client";

import { useEffect, useRef } from "react";
import { Lock } from "lucide-react";
import { MessageBubble } from "@/components/chat/message-bubble";
import { EmptyState } from "@/components/common/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePlatform } from "@/providers/platform-provider";

export function CustomerChat() {
  const { state, currentStep, mode } = usePlatform();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [state.customerMessages.length]);

  return (
    <section className="flex h-full min-h-0 flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-4 py-2">
        <h2 className="text-sm font-semibold">Customer Chat</h2>
        <p className="text-[11px] text-muted-foreground">
          {currentStep.exampleQuery
            ? `Example: ${currentStep.exampleQuery}`
            : "Journey traffic as domains appear and change"}
        </p>
      </div>

      <ScrollArea className="min-h-0 flex-1 px-3 py-3">
        {state.customerMessages.length === 0 ? (
          <EmptyState
            title="No customer traffic yet"
            description="Guided steps will run example requests as the architecture changes."
          />
        ) : (
          <div className="space-y-2.5">
            {state.customerMessages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={endRef} />
          </div>
        )}
      </ScrollArea>

      <div className="border-t border-border px-3 py-2">
        <div className="flex items-center gap-2 rounded-lg border border-dashed border-border bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
          <Lock className="size-3.5 shrink-0" />
          {mode === "demo"
            ? "Demo mode: queries are scripted by the guided steps."
            : "Live mode: customer input will be enabled when the backend is connected."}
        </div>
      </div>
    </section>
  );
}
