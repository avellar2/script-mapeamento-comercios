"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUpRight } from "@phosphor-icons/react";

const services = [
  {
    title: "Corte Masculino",
    desc: "Fade, undercut, social ou moderno. Finalização e hidratação inclusos.",
    price: "R$ 55",
    image: "https://images.unsplash.com/photo-1599351431202-0e67130d0cf5?w=600&h=800&fit=crop",
  },
  {
    title: "Barba Completa",
    desc: "Desenho, toalha quente, óleos e modelagem perfeita.",
    price: "R$ 40",
    image: "https://images.unsplash.com/photo-1621605815971-fbc98d665033?w=600&h=800&fit=crop",
  },
  {
    title: "Combo Corte + Barba",
    desc: "O clássico da casa com desconto exclusivo.",
    price: "R$ 85",
    image: "https://images.unsplash.com/photo-1503951912445-2b29b5f6f7d6?w=600&h=800&fit=crop",
  },
  {
    title: "Pigmentação",
    desc: "Disfarce de falhas e design de barba com micropigmentação.",
    price: "R$ 120",
    image: "https://images.unsplash.com/photo-1622286342621-4bd786c2448c?w=600&h=800&fit=crop",
  },
  {
    title: "Tratamento Capilar",
    desc: "Reconstrução, detox e hidratação profunda.",
    price: "R$ 70",
    image: "https://images.unsplash.com/photo-1567894340315-735d7e7f0c0e?w=600&h=800&fit=crop",
  },
  {
    title: "Pacote Mensal",
    desc: "4 cortes + 4 barbas. Prioridade de horário garantida.",
    price: "R$ 280",
    image: "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?w=600&h=800&fit=crop",
  },
];

export function Services() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  return (
    <section className="relative w-full px-6 py-32 md:px-12 lg:px-20">
      <div className="mx-auto max-w-[1400px]">
        <motion.div
          className="mb-20 flex flex-col items-start gap-4"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <p className="text-sm font-medium uppercase tracking-widest text-accent">
            Serviços & Preços
          </p>
          <h2 className="max-w-[20ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-6xl">
            O que fazemos.
          </h2>
        </motion.div>

        <div className="relative">
          {/* Floating image on hover */}
          <AnimatePresence>
            {hoveredIndex !== null && (
              <motion.div
                className="pointer-events-none absolute right-0 top-0 z-20 hidden h-[320px] w-[240px] overflow-hidden rounded-2xl shadow-2xl md:block"
                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: 20 }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                style={{ top: hoveredIndex * 90 }}
              >
                <img
                  src={services[hoveredIndex].image}
                  alt={services[hoveredIndex].title}
                  className="h-full w-full object-cover"
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex flex-col">
            {services.map((s, i) => (
              <motion.div
                key={s.title}
                className="group relative cursor-pointer border-t border-border-custom py-8 transition-colors duration-300 hover:bg-surface/50"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{
                  type: "spring",
                  stiffness: 100,
                  damping: 20,
                  delay: i * 0.06,
                }}
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6 md:gap-10">
                    <span className="text-sm font-mono text-text-muted">
                      0{i + 1}
                    </span>
                    <h3 className="text-2xl font-semibold text-text-primary transition-colors duration-300 group-hover:text-accent md:text-4xl">
                      {s.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-6">
                    <span className="hidden text-sm text-text-secondary md:block">
                      {s.desc}
                    </span>
                    <span className="text-xl font-bold text-accent md:text-2xl">
                      {s.price}
                    </span>
                    <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border-custom text-text-muted transition-all duration-300 group-hover:border-accent group-hover:bg-accent group-hover:text-background"
                    >
                      <ArrowUpRight size={18} weight="bold" />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
