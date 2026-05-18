"use client";

import { motion } from "framer-motion";

interface MarqueeProps {
  children: React.ReactNode;
  speed?: number;
  direction?: "left" | "right";
  dark?: boolean;
}

export function Marquee({ children, speed = 30, direction = "left", dark }: MarqueeProps) {
  return (
    <div className={`overflow-hidden whitespace-nowrap ${dark ? "border-y border-white/[0.06]" : "border-y border-slate-200/60"}`}>
      <motion.div
        className="inline-flex gap-12 py-5"
        animate={{ x: direction === "left" ? ["0%", "-50%"] : ["-50%", "0%"] }}
        transition={{ repeat: Infinity, duration: speed, ease: "linear" }}
      >
        {children}
        {children}
      </motion.div>
    </div>
  );
}
