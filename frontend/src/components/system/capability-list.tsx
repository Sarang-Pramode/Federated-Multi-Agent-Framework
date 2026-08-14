"use client";

import { motion, AnimatePresence } from "motion/react";
import type { SkillSnapshot } from "@/lib/types";

export function CapabilityList({
  skills,
  animate,
}: {
  skills: SkillSnapshot[];
  animate: boolean;
}) {
  if (skills.length === 0) {
    return (
      <p className="text-[11px] text-muted-foreground">No capabilities advertised</p>
    );
  }

  return (
    <ul className="flex flex-wrap gap-1">
      <AnimatePresence>
        {skills.map((skill) => (
          <motion.li
            key={skill.id}
            initial={animate ? { opacity: 0, scale: 0.9 } : false}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-md border border-primary/15 bg-primary/5 px-1.5 py-0.5 font-mono text-[10px] text-primary"
          >
            {skill.id}
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
