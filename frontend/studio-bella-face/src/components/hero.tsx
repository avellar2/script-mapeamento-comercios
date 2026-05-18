"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "@phosphor-icons/react";
import {
  fadeInUp,
  slideInRight,
  staggerContainer,
} from "./motion-variants";

export function Hero() {
  return (
    <section className="relative min-h-[100dvh] w-full overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-[#faf8f5] via-[#f5f0eb] to-[#faf8f5]" />

      <div className="relative z-10 mx-auto flex min-h-[100dvh] max-w-[1400px] flex-col items-center justify-center px-6 py-24 md:flex-row md:items-center md:justify-between md:px-12 lg:px-20">
        <motion.div
          className="flex w-full flex-col items-start gap-8 md:w-[52%] md:pr-12"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <motion.p
            variants={fadeInUp}
            className="text-sm font-medium uppercase tracking-widest text-accent"
          >
            Studio Bella Face
          </motion.p>

          <motion.h1
            variants={fadeInUp}
            className="max-w-[18ch] text-5xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-6xl lg:text-7xl"
          >
            Sua beleza,{" "}
            <span className="text-accent">tratada com arte.</span>
          </motion.h1>

          <motion.p
            variants={fadeInUp}
            className="max-w-[45ch] text-lg leading-relaxed text-text-secondary"
          >
            Manicure, sobrancelhas, cílios e cuidados faciais em um ambiente
            pensado para você. Atendimento personalizado, produtos premium e
            resultados que falam por si.
          </motion.p>

          <motion.a
            variants={fadeInUp}
            href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20agendar%20um%20hor%C3%A1rio."
            target="_blank"
            rel="noopener noreferrer"
            className="group mt-2 flex items-center gap-3 rounded-full bg-accent px-8 py-4 text-sm font-semibold text-white transition-transform duration-150 ease-out hover:bg-accent-dark active:scale-[0.98]"
            whileHover={{ scale: 1.02 }}
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

        <motion.div
          className="relative mt-16 w-full md:mt-0 md:w-[48%]"
          variants={slideInRight}
          initial="hidden"
          animate="visible"
        >
          <div className="relative mx-auto w-[85%] md:w-full">
            {/* Decorative blob behind the photo */}
            <div className="absolute -bottom-8 -left-8 h-[90%] w-[90%] rounded-[40%_60%_70%_30%/40%_50%_60%_50%] bg-accent/15 blur-2xl" />
            <div className="absolute -top-6 -right-6 h-[70%] w-[70%] rounded-[60%_40%_30%_70%/60%_30%_70%_40%] bg-accent-light/20 blur-2xl" />

            <div className="relative aspect-[3/4] w-full overflow-hidden rounded-[2rem] md:aspect-[4/5]">
              <img
                src="https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=800&q=80"
                alt="Juliana Ferreira — fundadora do Studio Bella Face"
                className="h-full w-full object-cover"
              />
            </div>

            <motion.div
              className="absolute -bottom-6 -left-4 z-20 rounded-2xl bg-white p-4 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.08)] md:-left-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, type: "spring", stiffness: 100, damping: 20 }}
            >
              <p className="text-xs font-medium text-text-muted uppercase tracking-wider">
                Profissional
              </p>
              <p className="text-lg font-semibold text-text-primary">
                Juliana Ferreira
              </p>
            </motion.div>

            <motion.div
              className="absolute -right-4 top-12 z-20 hidden rounded-2xl bg-accent p-4 text-white shadow-[0_20px_40px_-15px_rgba(184,125,107,0.4)] md:block md:-right-10"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1, type: "spring", stiffness: 100, damping: 20 }}
            >
              <p className="text-3xl font-bold">8+</p>
              <p className="text-xs opacity-80">anos de experiência</p>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
