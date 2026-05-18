"use client";

import { motion } from "framer-motion";
import { Star, Quote } from "lucide-react";

interface TestimonialCardProps {
  name: string;
  text: string;
  rating?: number;
  delay?: number;
  dark?: boolean;
}

export function TestimonialCard({ name, text, rating = 5, delay = 0, dark }: TestimonialCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className={`rounded-2xl p-6 border ${dark ? "bg-white/5 border-white/10" : "bg-white border-slate-200"} shadow-sm`}
    >
      <Quote size={20} className={`mb-3 ${dark ? "text-white/40" : "text-slate-300"}`} />
      <p className={`text-sm leading-relaxed mb-4 ${dark ? "text-slate-200" : "text-slate-700"}`}>{text}</p>
      <div className="flex items-center gap-1">
        {Array.from({ length: rating }).map((_, i) => (
          <Star key={i} size={14} className="text-amber-400 fill-amber-400" />
        ))}
      </div>
      <p className="mt-3 text-xs font-bold uppercase tracking-wide" style={{ opacity: 0.7 }}>
        {name}
      </p>
    </motion.div>
  );
}
