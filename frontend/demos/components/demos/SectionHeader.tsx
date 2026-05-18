"use client";

import { motion } from "framer-motion";

interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  accentColor: string;
  dark?: boolean;
}

export function SectionHeader({ eyebrow, title, description, accentColor, dark }: SectionHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5 }}
      className="text-center mb-10 md:mb-14"
    >
      {eyebrow && (
        <span className="inline-block text-xs font-bold tracking-widest uppercase mb-3" style={{ color: accentColor }}>
          {eyebrow}
        </span>
      )}
      <h2 className={`text-2xl md:text-3xl font-extrabold leading-tight ${dark ? "text-white" : "text-slate-900"}`}>
        {title}
      </h2>
      {description && (
        <p className={`mt-3 text-sm md:text-base max-w-xl mx-auto leading-relaxed ${dark ? "text-slate-300" : "text-slate-600"}`}>
          {description}
        </p>
      )}
    </motion.div>
  );
}
