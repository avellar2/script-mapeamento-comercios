"use client";

import { motion } from "framer-motion";

interface GalleryItem {
  title: string;
  subtitle?: string;
  color: string;
}

interface GalleryGridProps {
  items: GalleryItem[];
  dark?: boolean;
}

export function GalleryGrid({ items, dark }: GalleryGridProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
      {items.map((item, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: i * 0.08 }}
          className={`relative aspect-square rounded-2xl overflow-hidden flex flex-col items-center justify-center text-center p-4 ${dark ? "border border-white/10" : "border border-slate-200"}`}
          style={{ backgroundColor: item.color }}
        >
          <h4 className={`text-sm font-bold leading-tight ${dark ? "text-white" : "text-slate-900"}`}>{item.title}</h4>
          {item.subtitle && (
            <p className={`text-xs mt-1 ${dark ? "text-white/70" : "text-slate-600"}`}>{item.subtitle}</p>
          )}
        </motion.div>
      ))}
    </div>
  );
}
