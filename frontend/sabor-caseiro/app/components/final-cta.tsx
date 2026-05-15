"use client";

import { motion } from "framer-motion";
import { WhatsappLogo, ArrowRight, CookingPot } from "@phosphor-icons/react";

export function FinalCTA() {
  return (
    <section className="relative flex min-h-[50vh] w-full items-center justify-center overflow-hidden bg-wood">
      {/* Wood grain texture simulation */}
      <div className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: "repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0,0,0,0.1) 2px, rgba(0,0,0,0.1) 4px)",
        }}
      />

      <motion.div
        className="relative z-10 mx-auto max-w-[1400px] px-6 py-20 text-center md:px-12 lg:px-20"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      >
        {/* Neon sign style */}
        <div className="mx-auto mb-8 inline-flex items-center gap-4 rounded-lg border-4 border-yellow bg-red px-8 py-4 shadow-[0_0_30px_rgba(249,168,37,0.3)]">
          <CookingPot size={32} weight="fill" className="text-yellow" />
          <span className="text-2xl font-black tracking-widest text-yellow animate-neon md:text-3xl">
            HORA DE COMER!
          </span>
          <CookingPot size={32} weight="fill" className="text-yellow" />
        </div>

        <p className="mx-auto max-w-[45ch] text-lg leading-relaxed text-cream/80">
          Não fique com vontade. Faça seu pedido pelo WhatsApp e receba em minutos.
        </p>

        <motion.a
          href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20fazer%20um%20pedido."
          target="_blank"
          rel="noopener noreferrer"
          className="group mt-8 inline-flex items-center gap-3 rounded-full bg-[#25d366] px-10 py-5 text-sm font-bold text-white shadow-[0_6px_0_#128c7e] transition-all duration-150 ease-out hover:translate-y-[2px] hover:shadow-[0_3px_0_#128c7e] active:translate-y-[5px] active:shadow-none"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          <WhatsappLogo size={22} weight="fill" />
          Pedir Agora pelo WhatsApp
          <ArrowRight
            size={16}
            weight="bold"
            className="transition-transform duration-200 group-hover:translate-x-1"
          />
        </motion.a>
      </motion.div>
    </section>
  );
}
