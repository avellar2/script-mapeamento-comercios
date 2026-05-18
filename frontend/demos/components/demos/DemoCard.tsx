"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

interface DemoCardProps {
  slug: string;
  name: string;
  category: string;
  description: string;
  accentColor: string;
  bgColor: string;
}

export function DemoCard({ slug, name, category, description, accentColor, bgColor }: DemoCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="group rounded-2xl border border-slate-200 bg-white overflow-hidden hover:shadow-lg transition-shadow"
    >
      <div className="h-32 md:h-40 flex items-center justify-center relative overflow-hidden" style={{ backgroundColor: bgColor }}>
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-black to-transparent" />
        <motion.div
          className="text-4xl font-black tracking-tighter"
          style={{ color: accentColor }}
          whileHover={{ scale: 1.05 }}
        >
          {name.charAt(0)}
        </motion.div>
      </div>

      <div className="p-5">
        <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: accentColor }}>
          {category}
        </span>
        <h3 className="mt-1 text-lg font-extrabold text-slate-900 leading-tight">{name}</h3>
        <p className="mt-2 text-sm text-slate-600 leading-relaxed line-clamp-2">{description}</p>

        <Link
          href={`/demos/${slug}`}
          className="mt-4 inline-flex items-center gap-1 text-sm font-bold transition-colors hover:underline"
          style={{ color: accentColor }}
        >
          Ver demo
          <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </motion.div>
  );
}
