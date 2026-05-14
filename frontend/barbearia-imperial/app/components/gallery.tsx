"use client";

import { useRef } from "react";
import { motion } from "framer-motion";

const images = [
  { label: "Fade Americano", image: "https://images.unsplash.com/photo-1599351431202-0e67130d0cf5?w=600&h=800&fit=crop" },
  { label: "Barba Modelada", image: "https://images.unsplash.com/photo-1621605815971-fbc98d665033?w=600&h=800&fit=crop" },
  { label: "Corte Social", image: "https://images.unsplash.com/photo-1503951912445-2b29b5f6f7d6?w=600&h=800&fit=crop" },
  { label: "Pigmentação", image: "https://images.unsplash.com/photo-1622286342621-4bd786c2448c?w=600&h=800&fit=crop" },
  { label: "Tratamento", image: "https://images.unsplash.com/photo-1567894340315-735d7e7f0c0e?w=600&h=800&fit=crop" },
  { label: "Undercut", image: "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?w=600&h=800&fit=crop" },
  { label: "Navalhado", image: "https://images.unsplash.com/photo-1621605815971-fbc98d665033?w=600&h=800&fit=crop" },
];

export function Gallery() {
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <section className="relative w-full overflow-hidden py-32">
      <motion.div
        className="mb-16 px-6 md:px-12 lg:px-20"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      >
        <p className="mb-3 text-sm font-medium uppercase tracking-widest text-accent">Galeria</p>
        <h2 className="max-w-[18ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl">
          Os cortes que fazemos.
        </h2>
      </motion.div>

      {/* Coverflow Carousel 3D */}
      <div
        ref={scrollRef}
        className="flex snap-x snap-mandatory gap-6 overflow-x-auto px-6 pb-8 md:gap-8 md:px-12 lg:px-20"
        style={{
          perspective: "1200px",
          WebkitOverflowScrolling: "touch",
          scrollbarWidth: "none",
        }}
      >
        {images.map((img, i) => (
          <motion.div
            key={img.label + i}
            className="group relative shrink-0 snap-center"
            initial={{ opacity: 0, rotateY: 25 }}
            whileInView={{ opacity: 1, rotateY: 0 }}
            viewport={{ once: true }}
            transition={{
              type: "spring",
              stiffness: 100,
              damping: 20,
              delay: i * 0.05,
            }}
            style={{
              transformStyle: "preserve-3d",
              width: "clamp(260px, 40vw, 380px)",
            }}
          >
            <div className="relative aspect-[3/4] w-full overflow-hidden rounded-2xl">
              <img
                src={img.image}
                alt={img.label}
                className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-110"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
              <div className="absolute bottom-0 left-0 w-full p-6">
                <p className="text-xs font-medium uppercase tracking-widest text-accent">
                  Estilo
                </p>
                <h4 className="mt-1 text-xl font-semibold text-white">{img.label}</h4>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
