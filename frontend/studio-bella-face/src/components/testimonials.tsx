"use client";

import { motion } from "framer-motion";
import { Quotes } from "@phosphor-icons/react";
import { staggerContainer, fadeInUp } from "./motion-variants";

const testimonials = [
  {
    name: "Camila Rocha",
    role: "Cliente desde 2023",
    text: "A Camila que cuida das minhas unhas tem um olhar artistico impressionante. Cada esmaltação em gel dura semanas impecáveis. Não troco por nada.",
    initials: "CR",
    color: "bg-[#c9a99a]",
  },
  {
    name: "Fernanda Lima",
    role: "Designer de Interiores",
    text: "O ambiente já vale a visita. A limpeza de pele aqui é um ritual completo, com massagem facial e produtos que senti a diferença na primeira sessão.",
    initials: "FL",
    color: "bg-[#b87d6b]",
  },
  {
    name: "Juliana Mendes",
    role: "Empresária",
    text: "Minha sobrancelha nunca esteve tão simétrica e natural. A micropigmentação ficou tão sutil que minhas amigas acham que é pelo natural.",
    initials: "JM",
    color: "bg-[#a68a7b]",
  },
  {
    name: "Larissa Souza",
    role: "Influenciadora",
    text: "Extensão de cílios com durabilidade surreal. Durmo de lado, molho no banho e eles continuam perfeitos. Técnica impecável.",
    initials: "LS",
    color: "bg-[#8f7e72]",
  },
];

export function Testimonials() {
  return (
    <section className="relative w-full bg-surface-warm px-6 py-32 md:px-12 lg:px-20">
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
            Depoimentos
          </motion.p>
          <motion.h2
            variants={fadeInUp}
            className="max-w-[24ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl"
          >
            Quem experimenta, aprova.
          </motion.h2>
        </motion.div>

        <div className="flex snap-x snap-mandatory gap-5 overflow-x-auto pb-4 md:grid md:grid-cols-2 md:gap-6 lg:grid-cols-4">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              className="group relative min-w-[85vw] snap-center rounded-[1.5rem] bg-white p-7 shadow-[0_8px_32px_-12px_rgba(0,0,0,0.06)] transition-all duration-300 hover:shadow-[0_12px_40px_-12px_rgba(0,0,0,0.1)] md:min-w-0"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{
                type: "spring",
                stiffness: 100,
                damping: 20,
                delay: i * 0.08,
              }}
            >
              <Quotes
                size={28}
                weight="fill"
                className="mb-4 text-accent/20"
              />
              <p className="mb-6 text-base leading-relaxed text-text-secondary">
                {t.text}
              </p>

              <div className="flex items-center gap-4">
                <div
                  className={`flex h-11 w-11 items-center justify-center rounded-full text-xs font-bold text-white ${t.color}`}
                >
                  {t.initials}
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">
                    {t.name}
                  </p>
                  <p className="text-xs text-text-muted">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
