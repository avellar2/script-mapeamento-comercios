"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface ServiceCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  accentColor: string;
  delay?: number;
  dark?: boolean;
}

export function ServiceCard({ icon: Icon, title, description, accentColor, delay = 0, dark }: ServiceCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className={`rounded-2xl p-6 border transition-shadow hover:shadow-md ${dark ? "bg-white/5 border-white/10" : "bg-white border-slate-200"}`}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
        style={{ backgroundColor: `${accentColor}20` }}
      >
        <Icon size={20} style={{ color: accentColor }} />
      </div>
      <h3 className={`text-base font-bold mb-1 ${dark ? "text-white" : "text-slate-900"}`}>{title}</h3>
      <p className={`text-sm leading-relaxed ${dark ? "text-slate-300" : "text-slate-600"}`}>{description}</p>
    </motion.div>
  );
}
