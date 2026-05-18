"use client";

import { useRef, useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface TiltCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  accentColor: string;
  delay?: number;
  dark?: boolean;
}

export function TiltCard({ icon: Icon, title, description, accentColor, delay = 0, dark }: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.5);

  const rotateX = useSpring(useTransform(y, [0, 1], [8, -8]), { stiffness: 200, damping: 20 });
  const rotateY = useSpring(useTransform(x, [0, 1], [-8, 8]), { stiffness: 200, damping: 20 });
  const glareX = useTransform(x, [0, 1], ["0%", "100%"]);
  const glareY = useTransform(y, [0, 1], ["0%", "100%"]);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    x.set((e.clientX - rect.left) / rect.width);
    y.set((e.clientY - rect.top) / rect.height);
  };

  const handleMouseLeave = () => {
    x.set(0.5);
    y.set(0.5);
  };

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d", perspective: 1000 }}
      className={`relative rounded-2xl p-6 border overflow-hidden ${dark ? "bg-white/[0.03] border-white/[0.08]" : "bg-white border-slate-200/60"} shadow-[0_8px_32px_-12px_rgba(0,0,0,0.1)]`}
    >
      <motion.div
        className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{ background: `radial-gradient(circle at ${glareX} ${glareY}, ${accentColor}10, transparent 50%)` }}
      />
      <div className="relative z-10" style={{ transform: "translateZ(20px)" }}>
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
          style={{ backgroundColor: `${accentColor}15` }}
        >
          <Icon size={22} style={{ color: accentColor }} strokeWidth={2} />
        </div>
        <h3 className={`text-lg font-bold mb-2 ${dark ? "text-white" : "text-slate-900"}`}>{title}</h3>
        <p className={`text-sm leading-relaxed ${dark ? "text-slate-400" : "text-slate-600"}`}>{description}</p>
      </div>
    </motion.div>
  );
}
