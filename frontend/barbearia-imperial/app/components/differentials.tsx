"use client";

import { motion } from "framer-motion";

const stats = [
  { num: "8+", label: "Anos de experiência", desc: "Desde 2015 cuidando do visual masculino" },
  { num: "12K+", label: "Clientes atendidos", desc: "Homens que voltam e indicam" },
  { num: "47", label: "Minutos por corte", desc: "Tempo médio sem pressa, com capricho" },
  { num: "4.9", label: "Avaliação média", desc: "Baseado em +800 reviews no Google" },
];

const features = [
  "Toalha quente aromatizada",
  "Playlist curada rap/hip-hop",
  "Cerveja artesanal inclusa",
  "Produtos importados",
  "Agendamento sem fila",
  "Ambiente climatizado",
];

export function Differentials() {
  return (
    <section className="relative w-full px-6 py-32 md:px-12 lg:px-20">
      <div className="mx-auto max-w-[1400px]">
        <motion.div
          className="mb-16 flex flex-col items-start gap-4"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <p className="text-sm font-medium uppercase tracking-widest text-accent">Por que a Imperial</p>
          <h2 className="max-w-[18ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-6xl">
            Números que importam.
          </h2>
        </motion.div>

        {/* Stats Bento Grid */}
        <div className="mb-20 grid grid-cols-2 gap-4 md:grid-cols-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              className="group relative overflow-hidden rounded-[1.5rem] bg-surface p-6 transition-all duration-300 hover:bg-surface-elevated md:p-8"
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
              <p className="mb-2 font-mono text-4xl font-bold text-accent md:text-5xl">
                {s.num}
              </p>
              <p className="mb-1 text-sm font-semibold text-text-primary">{s.label}</p>
              <p className="text-xs leading-relaxed text-text-muted">{s.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Features marquee strip */}
        <motion.div
          className="relative overflow-hidden rounded-[1.5rem] border border-border-custom bg-surface py-6"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <div className="flex animate-marquee whitespace-nowrap">
            {[...features, ...features, ...features].map((f, i) => (
              <span
                key={i}
                className="mx-8 inline-flex items-center gap-3 text-sm font-medium text-text-secondary"
              >
                <span className="h-2 w-2 rounded-full bg-accent" />
                {f}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
