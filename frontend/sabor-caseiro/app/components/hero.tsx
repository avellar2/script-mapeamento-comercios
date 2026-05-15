"use client";

import { motion } from "framer-motion";
import { ArrowRight, CookingPot } from "@phosphor-icons/react";

export function Hero() {
  return (
    <section className="relative flex min-h-[100dvh] w-full items-center overflow-hidden bg-cream">
      {/* Tile pattern overlay */}
      <div className="absolute inset-0 tile-pattern" />

      {/* Wood beam top */}
      <div className="absolute left-0 right-0 top-0 h-4 bg-wood shadow-lg" />

      <div className="relative z-10 mx-auto flex w-full max-w-[1400px] flex-col items-center gap-8 px-6 py-20 md:flex-row md:items-center md:justify-between md:px-12 lg:px-20">
        {/* Left: Boteco sign + text */}
        <motion.div
          className="flex flex-col items-center gap-6 md:items-start md:max-w-[55%]"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          {/* Neon boteco sign */}
          <div className="relative rounded-lg bg-red px-6 py-3 shadow-[0_0_20px_rgba(198,40,40,0.4)]">
            <div className="flex items-center gap-3">
              <CookingPot size={28} weight="fill" className="text-yellow" />
              <span className="text-lg font-bold tracking-widest text-yellow animate-neon">
                ABRASILEIRADO
              </span>
              <CookingPot size={28} weight="fill" className="text-yellow" />
            </div>
            {/* Light bulbs decoration */}
            <div className="absolute -left-1 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-yellow shadow-[0_0_8px_#F9A825]" />
            <div className="absolute -right-1 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-yellow shadow-[0_0_8px_#F9A825]" />
          </div>

          <h1 className="text-center text-5xl font-black leading-[0.9] tracking-tight text-wood md:text-left md:text-7xl lg:text-8xl"
            style={{ textShadow: "3px 3px 0px rgba(198,40,40,0.15)" }}
          >
            Comida de
            <br />
            <span className="text-red">verdade</span>,
            <br />
            sabor de casa.
          </h1>

          <p className="max-w-[40ch] text-center text-lg leading-relaxed text-text-secondary md:text-left">
            Marmitaria caseira que lembra a cozinha da vovó. Arroz soltinho, feijão
            no ponto e carne bem temperada. Sem frescura, sem industrializado.
          </p>

          <motion.a
            href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20fazer%20um%20pedido."
            target="_blank"
            rel="noopener noreferrer"
            className="group mt-2 inline-flex items-center gap-3 rounded-lg bg-accent px-8 py-4 text-sm font-bold text-white shadow-[0_4px_0_#1b5e20] transition-all duration-150 ease-out hover:translate-y-[2px] hover:shadow-[0_2px_0_#1b5e20] active:translate-y-[4px] active:shadow-none"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Fazer Pedido pelo WhatsApp
            <ArrowRight
              size={16}
              weight="bold"
              className="transition-transform duration-200 group-hover:translate-x-1"
            />
          </motion.a>

          {/* Trust badges on wood planks */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3 md:justify-start">
            {["Arroz soltinho", "Feijão fresco", "Entrega rápida"].map((tag) => (
              <span
                key={tag}
                className="rounded bg-wood px-3 py-1.5 text-xs font-semibold text-cream shadow-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        </motion.div>

        {/* Right: Rotating bandeja showcase */}
        <motion.div
          className="relative flex items-center justify-center md:w-[45%]"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 80, damping: 20, delay: 0.3 }}
        >
          {/* Main bandeja */}
          <div className="relative h-[300px] w-[300px] overflow-hidden rounded-2xl border-4 border-surface-elevated bg-surface shadow-2xl md:h-[380px] md:w-[380px]"
            style={{ boxShadow: "inset 0 0 30px rgba(0,0,0,0.1), 0 20px 50px rgba(0,0,0,0.2)" }}
          >
            {/* Metallic shine overlay */}
            <div className="absolute inset-0 z-10 animate-bandeja-shine pointer-events-none" />
            <img
              src="https://picsum.photos/seed/prato-brasil/800/800"
              alt="Prato brasileiro caseiro"
              className="h-full w-full object-cover"
            />
            {/* Steam wisps */}
            <div className="absolute left-1/4 top-8 h-12 w-8 rounded-full bg-white/30 blur-xl animate-steam" />
            <div className="absolute left-1/2 top-6 h-16 w-10 rounded-full bg-white/20 blur-xl animate-steam" style={{ animationDelay: "0.7s" }} />
          </div>

          {/* Decorative wooden plate under */}
          <div className="absolute -bottom-3 left-1/2 h-8 w-[90%] -translate-x-1/2 rounded-full bg-wood/20 blur-md" />

          {/* Price tag hanging */}
          <motion.div
            className="absolute -right-4 top-8 rotate-12 rounded-lg bg-yellow px-3 py-2 shadow-lg md:right-0"
            animate={{ rotate: [12, 8, 12] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <p className="text-xs font-bold text-wood">A partir de</p>
            <p className="text-xl font-black text-red">R$ 19,90</p>
          </motion.div>
        </motion.div>
      </div>

      {/* Lona wave bottom */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 80" preserveAspectRatio="none" className="h-16 w-full md:h-20">
          <path
            d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z"
            fill="#d7ccc8"
          />
          <path
            d="M0,50 C240,85 480,15 720,50 C960,85 1200,15 1440,50 L1440,80 L0,80 Z"
            fill="rgba(161,136,127,0.3)"
          />
        </svg>
      </div>
    </section>
  );
}
