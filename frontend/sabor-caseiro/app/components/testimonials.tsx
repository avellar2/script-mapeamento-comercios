"use client";

import { motion } from "framer-motion";
import { Star } from "@phosphor-icons/react";

const testimonials = [
  {
    id: 1,
    name: "Marcio Teixeira",
    text: "Compro aqui toda semana. A feijoada de sexta é sagrada.",
    rating: 5,
    color: "#E8F5E9",
    magnet: "#4CAF50",
  },
  {
    id: 2,
    name: "Fernanda Lopes",
    text: "Minhas crianças comem sem reclamar. Comida de verdade.",
    rating: 5,
    color: "#FFF3E0",
    magnet: "#FF9800",
  },
  {
    id: 3,
    name: "Ricardo Amorim",
    text: "Almoço aqui de segunda a sexta. Rápido, gostoso e barato.",
    rating: 5,
    color: "#E3F2FD",
    magnet: "#2196F3",
  },
  {
    id: 4,
    name: "Juliana Costa",
    text: "O combo família salvou nossos almoços de domingo.",
    rating: 5,
    color: "#FCE4EC",
    magnet: "#E91E63",
  },
  {
    id: 5,
    name: "Anderson Melo",
    text: "Sou exigente e aprovado. O strogonoff tem o ponto certo.",
    rating: 5,
    color: "#F3E5F5",
    magnet: "#9C27B0",
  },
  {
    id: 6,
    name: "Patricia Nunes",
    text: "Pedido pelo WhatsApp, entrega rápida e comida quente.",
    rating: 5,
    color: "#E0F2F1",
    magnet: "#009688",
  },
];

function RecadoCard({ t, index }: { t: typeof testimonials[0]; index: number }) {
  const rotations = [-3, 2, -1, 3, -2, 1];
  const yOffsets = [0, -8, 4, -4, 6, -2];

  return (
    <motion.div
      className="relative w-[280px] shrink-0 p-5 shadow-lg md:w-[320px]"
      style={{
        background: t.color,
        transform: `rotate(${rotations[index]}deg)`,
        marginTop: yOffsets[index],
      }}
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ type: "spring", stiffness: 200, damping: 15, delay: index * 0.1 }}
      whileHover={{ rotate: 0, scale: 1.05, zIndex: 10 }}
    >
      {/* Magnet */}
      <div
        className="absolute -top-3 left-1/2 h-6 w-8 -translate-x-1/2 rounded-sm shadow-md"
        style={{ background: t.magnet }}
      />

      {/* Tape on corner */}
      <div className="absolute -right-2 -top-2 h-8 w-12 rotate-12 bg-yellow/60 shadow-sm"
        style={{ clipPath: "polygon(0 0, 100% 0, 85% 100%, 15% 100%)" }}
      />

      <div className="flex items-center gap-1">
        {Array.from({ length: t.rating }).map((_, i) => (
          <Star key={i} size={14} weight="fill" className="text-yellow" />
        ))}
      </div>

      <p className="mt-3 text-base leading-relaxed text-wood">
        "{t.text}"
      </p>

      <div className="mt-4 flex items-center gap-2">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm"
          style={{ background: t.magnet }}
        >
          {t.name.split(" ").map((n) => n[0]).join("")}
        </div>
        <p className="text-sm font-semibold text-text-secondary">
          {t.name}
        </p>
      </div>
    </motion.div>
  );
}

export function Testimonials() {
  return (
    <section className="relative w-full overflow-hidden bg-cream py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-6 md:px-12 lg:px-20">
        <motion.div
          className="mb-12 flex flex-col items-center gap-3"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <p className="text-sm font-bold uppercase tracking-widest text-accent">
            Quem come, volta.
          </p>
          <h2 className="text-center text-4xl font-black leading-[0.9] tracking-tight text-wood md:text-5xl">
            Recados na geladeira.
          </h2>
        </motion.div>
      </div>

      {/* Recados grid */}
      <div className="flex flex-wrap justify-center gap-6 px-6 md:gap-8">
        {testimonials.map((t, i) => (
          <RecadoCard key={t.id} t={t} index={i} />
        ))}
      </div>
    </section>
  );
}
