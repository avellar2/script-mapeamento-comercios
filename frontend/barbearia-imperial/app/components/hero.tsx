"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "@phosphor-icons/react";

export function Hero() {
  return (
    <section className="relative flex min-h-[100dvh] w-full items-center justify-center overflow-hidden">
      {/* Background Image with Ken Burns effect */}
      <div className="absolute inset-0 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=1920&q=80"
          alt="Barbearia"
          className="absolute inset-0 h-full w-full object-cover animate-ken-burns"
        />
      </div>

      <div className="absolute inset-0 bg-black/60" />

      <div className="relative z-10 mx-auto flex w-full max-w-[1400px] flex-col items-center justify-center px-6 py-24 text-center">
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mb-6 text-sm font-medium uppercase tracking-[0.3em] text-accent"
        >
          Barbearia Imperial
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, type: "spring", stiffness: 80, damping: 20 }}
          className="relative mb-8"
        >
          <span
            className="block text-[15vw] font-bold leading-[0.85] tracking-tighter text-white md:text-[12vw]"
            style={{
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
              backgroundImage:
                "url('https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=1920&q=80')",
              backgroundSize: "cover",
              backgroundPosition: "center",
              WebkitTextStroke: "1px rgba(255,255,255,0.1)",
            }}
          >
            IMPERIAL
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="mb-10 max-w-[50ch] text-lg leading-relaxed text-white/70 md:text-xl"
        >
          Corte, barba e atitude. Desde 2015 elevando o padrão da barbearia em São Paulo.
        </motion.p>

        <motion.a
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1, duration: 0.6 }}
          href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20agendar%20um%20corte."
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-3 rounded-full bg-accent px-10 py-5 text-sm font-semibold text-background transition-transform duration-150 ease-out hover:bg-accent-light active:scale-[0.98]"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          Agendar corte pelo WhatsApp
          <ArrowRight
            size={18}
            weight="bold"
            className="transition-transform duration-200 group-hover:translate-x-1"
          />
        </motion.a>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="h-12 w-[1px] bg-gradient-to-b from-transparent via-accent to-transparent" />
      </motion.div>
    </section>
  );
}
