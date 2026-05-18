"use client";

import { motion } from "framer-motion";
import { Sparkle, Plant, Heart, Clock } from "@phosphor-icons/react";
import { staggerContainer, fadeInUp } from "./motion-variants";

const items = [
  {
    num: "01",
    icon: Sparkle,
    title: "Ambiente Premium",
    desc: "Espaço pensado para seu conforto, com aromaterapia, iluminação suave e música de fundo que transforma cada visita em um ritual de bem-estar.",
  },
  {
    num: "02",
    icon: Plant,
    title: "Produtos Selecionados",
    desc: "Trabalhamos apenas com marcas cruelty-free, hipoalergênicas e importadas. Sua pele merece o que existe de melhor no mercado.",
  },
  {
    num: "03",
    icon: Heart,
    title: "Atendimento Personalizado",
    desc: "Cada cliente recebe uma avaliação exclusiva antes do procedimento. Não fazemos protocolos padronizados — fazemos protocolos sob medida.",
  },
  {
    num: "04",
    icon: Clock,
    title: "Horário Flexível",
    desc: "Agendamentos online com confirmação imediata pelo WhatsApp. Atendemos de terça a sábado, incluindo horários alternativos para sua rotina.",
  },
];

export function Differentials() {
  return (
    <section className="relative w-full overflow-hidden bg-surface-warm px-6 py-32 md:px-12 lg:px-20">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-20">
        {/* Left — Image */}
        <motion.div
          className="relative aspect-[3/4] w-full overflow-hidden rounded-[2rem] lg:aspect-[4/5]"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ type: "spring", stiffness: 80, damping: 20 }}
        >
          <img
            src="https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=800&q=80"
            alt="Ambiente do Studio Bella Face"
            className="h-full w-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />
          <div className="absolute bottom-8 left-8">
            <p className="text-sm font-medium uppercase tracking-widest text-white/70">
              Desde 2017
            </p>
            <p className="mt-1 text-3xl font-semibold text-white">
              Cuidando de você
            </p>
          </div>
        </motion.div>

        {/* Right — Differentials List */}
        <motion.div
          className="flex flex-col"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.div className="mb-10 flex flex-col gap-3" variants={fadeInUp}>
            <p className="text-sm font-medium uppercase tracking-widest text-accent">
              Por que nos escolher
            </p>
            <h2 className="max-w-[16ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl">
              O cuidado que você merece.
            </h2>
          </motion.div>

          <div className="flex flex-col">
            {items.map((item, i) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.num}
                  className="group flex items-start gap-5 border-t border-border-custom py-7 transition-colors duration-300 first:border-t-0"
                  initial={{ opacity: 0, x: 24 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{
                    type: "spring",
                    stiffness: 100,
                    damping: 20,
                    delay: i * 0.1,
                  }}
                >
                  <span className="mt-1 text-xs font-medium text-text-muted">
                    {item.num}
                  </span>

                  <div className="flex flex-1 items-start gap-5">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent/10 text-accent transition-all duration-300 group-hover:bg-accent group-hover:text-white"
                    >
                      <Icon size={24} weight="duotone" />
                    </div>

                    <div className="flex flex-col gap-1">
                      <h3 className="text-lg font-semibold text-text-primary">
                        {item.title}
                      </h3>
                      <p className="max-w-[40ch] text-sm leading-relaxed text-text-secondary">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
