"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "@phosphor-icons/react";
import { staggerContainer, fadeInUp } from "./motion-variants";

export function FinalCTA() {
  return (
    <section className="relative w-full overflow-hidden bg-accent px-6 py-28 md:px-12 lg:px-20">
      {/* Subtle texture */}
      <div className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />

      <motion.div
        className="relative z-10 mx-auto flex max-w-[1400px] flex-col items-start gap-8 md:flex-row md:items-end md:justify-between"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={staggerContainer}
      >
        <div className="flex flex-col items-start gap-6">
          <motion.h2
            variants={fadeInUp}
            className="max-w-[16ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-white md:text-6xl"
          >
            Pronta para se sentir ainda mais bela?
          </motion.h2>
          <motion.p
            variants={fadeInUp}
            className="max-w-[45ch] text-lg leading-relaxed text-white/80"
          >
            Agende seu horário agora mesmo pelo WhatsApp. Atendimento
            personalizado, sem filas e com a conveniência que você merece.
          </motion.p>
        </div>

        <motion.a
          variants={fadeInUp}
          href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20agendar%20um%20hor%C3%A1rio."
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-3 rounded-full bg-white px-8 py-4 text-sm font-semibold text-accent transition-transform duration-150 ease-out active:scale-[0.98]"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          Agendar pelo WhatsApp
          <ArrowRight
            size={18}
            weight="bold"
            className="transition-transform duration-200 group-hover:translate-x-1"
          />
        </motion.a>
      </motion.div>
    </section>
  );
}
