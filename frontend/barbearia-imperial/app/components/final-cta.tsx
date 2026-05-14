"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "@phosphor-icons/react";

export function FinalCTA() {
  return (
    <section className="relative flex min-h-[60vh] w-full items-center justify-center overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1585747860715-2ba37e788b70?w=1920&h=1080&fit=crop')",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-background/95 via-background/80 to-background/60" />

      <motion.div
        className="relative z-10 mx-auto max-w-[1400px] px-6 py-28 text-center md:px-12 lg:px-20"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      >
        <h2 className="mx-auto max-w-[16ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-6xl">
          Agora é sua vez de sentir a diferença.
        </h2>

        <p className="mx-auto mt-6 max-w-[45ch] text-lg leading-relaxed text-text-secondary">
          Agenda pelo WhatsApp. Sem fila, sem enrolação. Chega no horário e
          sai no ponto.
        </p>

        <motion.a
          href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20agendar%20um%20corte."
          target="_blank"
          rel="noopener noreferrer"
          className="group mt-10 inline-flex items-center gap-3 rounded-full bg-accent px-10 py-5 text-sm font-semibold text-background transition-transform duration-150 ease-out hover:bg-accent-light active:scale-[0.98]"
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
