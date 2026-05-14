"use client";

import { motion } from "framer-motion";

const testimonials = [
  {
    name: "Thiago Nunes",
    role: "Cliente desde 2022",
    text: "O Ricardo entende de cabelo como ninguém. Saio daqui sempre com um fade perfeito.",
  },
  {
    name: "Lucas Mendonça",
    role: "Empresário",
    text: "Levo meu filho pra cortar aqui. O ambiente é massa e a galera é receptiva.",
  },
  {
    name: "André Costa",
    role: "Designer",
    text: "A pigmentação de barba mudou minha vida. Disfarçou falhas que eu tinha desde os 25.",
  },
  {
    name: "Bruno Oliveira",
    role: "Personal Trainer",
    text: "Pacote mensal vale demais. Corte no ponto, zero fila e cerveja artesanal.",
  },
  {
    name: "Felipe Rocha",
    role: "Engenheiro",
    text: "Primeira vez que encontro uma barbearia que respeita o horário. Ponto final.",
  },
  {
    name: "Gabriel Santos",
    role: "Músico",
    text: "Playlist de hip-hop, toalha quente e um corte impecável. Meu lugar favorito.",
  },
];

export function Testimonials() {
  const doubled = [...testimonials, ...testimonials];

  return (
    <section className="relative w-full overflow-hidden bg-surface py-32">
      <motion.div
        className="mb-12 px-6 md:px-12 lg:px-20"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      >
        <p className="mb-3 text-sm font-medium uppercase tracking-widest text-accent">Depoimentos</p>
        <h2 className="max-w-[16ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl">
          Quem vem, volta.
        </h2>
      </motion.div>

      {/* Infinite Marquee */}
      <div className="relative flex overflow-hidden">
        <div className="flex animate-marquee-slow whitespace-nowrap">
          {doubled.map((t, i) => (
            <div
              key={i}
              className="mx-4 inline-block w-[380px] shrink-0 rounded-[1.5rem] bg-background p-7 md:mx-6 md:w-[420px]"
            >
              <p className="mb-6 text-base leading-relaxed text-text-secondary">
                "{t.text}"
              </p>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-xs font-bold text-background"
                >
                  {t.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">{t.name}</p>
                  <p className="text-xs text-text-muted">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
