"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Star, Quote } from "lucide-react";
import type { ClientData, Testimonial } from "@/types/client";

export default function TestimonialsSection({ data }: { data: ClientData }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const titles = data.sectionTitles || {};
  const title = titles.testimonials || "Depoimentos";
  const subtitle = titles.testimonialsSubtitle || "O que nossos clientes dizem";
  const description = (titles as Record<string, string>).testimonialsDescription || "";
  const testimonials = data.testimonials || [];

  if (testimonials.length === 0) return null;

  return (
    <section id="depoimentos" className="py-20 md:py-32 bg-surface" ref={ref}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="text-center max-w-2xl mx-auto mb-12 md:mb-16"
        >
          <span className="text-sm font-semibold text-primary uppercase tracking-wider">{title}</span>
          <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900">
            {subtitle}
          </h2>
          {description && (
            <p className="mt-4 text-base md:text-lg text-muted leading-relaxed">{description}</p>
          )}
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {testimonials.map((t: Testimonial, i: number) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: "spring", stiffness: 100, damping: 20, delay: i * 0.12 }}
              className="relative flex flex-col gap-5 p-6 md:p-8 bg-white rounded-[1.5rem] border border-border"
            >
              <div className="absolute top-6 right-6 text-primary/10">
                <Quote size={40} fill="currentColor" />
              </div>

              <div className="flex gap-1">
                {Array.from({ length: t.rating }).map((_, r) => (
                  <Star key={r} size={16} fill="currentColor" className="text-amber-400" />
                ))}
              </div>

              <p className="text-base text-slate-700 leading-relaxed flex-1">&ldquo;{t.text}&rdquo;</p>

              <div className="flex items-center gap-3 pt-2 border-t border-border">
                <img
                  src={t.image}
                  alt={t.name}
                  className="w-10 h-10 rounded-full object-cover"
                />
                <div>
                  <p className="text-sm font-semibold text-slate-900">{t.name}</p>
                  <p className="text-xs text-muted">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}