"use client";

import { motion } from "framer-motion";
import { staggerContainer, fadeInUp } from "./motion-variants";

const images = [
  { seed: "bella-galeria-1", label: "Manicure em Gel", image: "https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=600&q=80" },
  { seed: "bella-galeria-2", label: "Design de Sobrancelhas", image: "https://images.unsplash.com/photo-1522337660859-02fbefca4708?auto=format&fit=crop&w=600&q=80" },
  { seed: "bella-galeria-3", label: "Extensão de Cílios", image: "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=600&q=80" },
  { seed: "bella-galeria-4", label: "Limpeza de Pele", image: "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=600&q=80" },
  { seed: "bella-galeria-5", label: "Depilação com Cera", image: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80" },
  { seed: "bella-galeria-6", label: "Tratamento Facial", image: "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?auto=format&fit=crop&w=600&q=80" },
];

export function Gallery() {
  return (
    <section className="relative w-full px-6 py-32 md:px-12 lg:px-20">
      <div className="mx-auto max-w-[1400px]">
        <motion.div
          className="mb-16 flex flex-col items-start gap-4"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.p
            variants={fadeInUp}
            className="text-sm font-medium uppercase tracking-widest text-accent"
          >
            Galeria
          </motion.p>
          <motion.h2
            variants={fadeInUp}
            className="max-w-[20ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl"
          >
            Momentos de transformação.
          </motion.h2>
        </motion.div>

        {/* Desktop — Accordion Image Slider (hover-based) */}
        <motion.div
          className="hidden h-[520px] w-full gap-3 md:flex"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={staggerContainer}
        >
          {images.map((img) => (
            <motion.div
              key={img.seed}
              className="group relative h-full flex-1 cursor-pointer overflow-hidden rounded-[1.5rem] transition-all duration-700 ease-out hover:flex-[3]"
              variants={fadeInUp}
            >
              <img
                src={img.image}
                alt={img.label}
                className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
              <div className="absolute bottom-0 left-0 w-full p-8 opacity-0 transition-all duration-500 group-hover:opacity-100">
                <p className="text-sm font-medium uppercase tracking-wider text-white/70">
                  Procedimento
                </p>
                <h4 className="mt-1 text-xl font-semibold text-white">
                  {img.label}
                </h4>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Mobile — Grid (touch-friendly) */}
        <motion.div
          className="grid grid-cols-2 gap-3 md:hidden"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={staggerContainer}
        >
          {images.map((img) => (
            <motion.div
              key={img.seed}
              className="group relative aspect-square overflow-hidden rounded-[1rem]"
              variants={fadeInUp}
            >
              <img
                src={img.image}
                alt={img.label}
                className="h-full w-full object-cover"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
              <div className="absolute bottom-0 left-0 w-full p-3">
                <p className="text-xs font-medium uppercase tracking-wider text-white/70">
                  Procedimento
                </p>
                <h4 className="mt-0.5 text-sm font-semibold text-white">
                  {img.label}
                </h4>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
