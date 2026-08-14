"use client";

import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[90%] rounded-2xl px-3 py-2 text-sm leading-relaxed shadow-sm",
          isUser
            ? "rounded-br-md bg-primary text-primary-foreground"
            : "rounded-bl-md border border-border bg-card text-foreground",
        )}
      >
        <p>{message.content}</p>
        <p
          className={cn(
            "mt-1 font-mono text-[10px]",
            isUser ? "text-primary-foreground/70" : "text-muted-foreground",
          )}
        >
          {message.timestamp}
        </p>
      </div>
    </div>
  );
}
