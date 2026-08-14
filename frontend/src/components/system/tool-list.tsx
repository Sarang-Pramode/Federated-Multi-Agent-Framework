"use client";

import { motion, AnimatePresence } from "motion/react";
import type { ToolSnapshot } from "@/lib/types";

export function ToolList({
  tools,
  animate,
}: {
  tools: ToolSnapshot[];
  animate: boolean;
}) {
  if (tools.length === 0) {
    return <p className="text-[11px] text-muted-foreground">No tools registered</p>;
  }

  return (
    <ul className="flex flex-wrap gap-1">
      <AnimatePresence>
        {tools.map((tool) => (
          <motion.li
            key={tool.name}
            initial={animate ? { opacity: 0, y: 4 } : false}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-md border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground"
            title={`schema ${tool.schemaHash}`}
          >
            {tool.name}
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
