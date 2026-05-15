"use client";

import { useRef } from "react";
import { motion } from "framer-motion";
import { Fire, CaretLeft, CaretRight } from "@phosphor-icons/react";

const dishes = [
  {
    id: 1,
    name: "Strogonoff de Frango",
    desc: "Arroz soltinho, batata palha e molho cremoso.",
    price: "R$ 24,90",
    image: "https://picsum.photos/seed/strogonoff-br/600/800",
    tag: "Mais pedido",
  },
  {
    id: 2,
    name: "Feijoada Completa",
    desc: "Feijão preto, linguiça, costelinha e couve.",
    price: "R$ 31,00",
    image: "https://picsum.photos/seed/feijoada-br/600/800",
    tag: null,
  },
  {
    id: 3,
    name: "Bife Acebolado",
    desc: "Contra-filé com cebola caramelizada e purê.",
    price: "R$ 28,50",
    image: "https://picsum.photos/seed/bife-br/600/800",
    tag: null,
  },
  {
    id: 4,
    name: "Frango à Parmegiana",
    desc: "Empanado, molho de tomate e queijo derretido.",
    price: "R$ 26,90",
    image: "https://picsum.photos/seed/parmegiana-br/600/800",
    tag: "Top 3",
  },
  {
    id: 5,
    name: "Filé de Tilápia",
    desc: "Grelhado com arroz integral e legumes.",
    price: "R$ 27,90",
    image: "https://picsum.photos/seed/peixe-br/600/800",
    tag: null,
  },
];

export function Dishes() {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (dir: "left" | "right") => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir === "left" ? -320 : 320, behavior: "smooth" });
    }
  };

  return (
    <section className="relative w-full overflow-hidden bg-surface py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-6 md:px-12 lg:px-20">
        <motion.div
          className="mb-10 flex items-end justify-between"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <div className="flex flex-col gap-3">
            <p className="text-sm font-bold uppercase tracking-widest text-accent">
              Pratos do Dia
            </p>
            <h2 className="max-w-[20ch] text-4xl font-black leading-[0.9] tracking-tight text-wood md:text-5xl">
              Passe e escolha.
            </h2>
          </div>
          <div className="hidden gap-2 md:flex">
            <button
              onClick={() => scroll("left")}
              className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-wood bg-cream text-wood transition-colors hover:bg-wood hover:text-cream"
            >
              <CaretLeft size={20} weight="bold" />
            </button>
            <button
              onClick={() => scroll("right")}
              className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-wood bg-cream text-wood transition-colors hover:bg-wood hover:text-cream"
            >
              <CaretRight size={20} weight="bold" />
            </button>
          </div>
        </motion.div>
      </div>

      {/* Conveyor belt of bandejas */}
      <div
        ref={scrollRef}
        className="flex gap-5 overflow-x-auto px-6 pb-6 md:gap-8 md:px-12 lg:px-20"
        style={{
          scrollbarWidth: "none",
          WebkitOverflowScrolling: "touch",
        }}
      >
        {dishes.map((dish, i) => (
          <motion.div
            key={dish.id}
            className="group relative shrink-0"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{
              type: "spring",
              stiffness: 100,
              damping: 20,
              delay: i * 0.08,
            }}
            style={{ width: "clamp(260px, 35vw, 320px)" }}
          >
            {/* Bandeja container */}
            <div className="relative overflow-hidden rounded-xl border-2 border-surface-elevated bg-surface-elevated shadow-[0_8px_0_rgba(93,64,55,0.2)]">
              {/* Metallic rim */}
              <div className="absolute inset-x-0 top-0 z-10 h-2 bg-gradient-to-b from-white/40 to-transparent" />
              <img
                src={dish.image}
                alt={dish.name}
                className="aspect-[4/3] w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />

              {dish.tag && (
                <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded bg-red px-2.5 py-1 text-xs font-bold text-white shadow-sm">
                  <Fire size={12} weight="fill" />
                  {dish.tag}
                </div>
              )}

              {/* Content on bandeja */}
              <div className="relative border-t-2 border-dashed border-border p-4">
                <h3 className="text-lg font-black text-wood">
                  {dish.name}
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-text-secondary">
                  {dish.desc}
                </p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="font-mono text-xl font-bold text-accent">
                    {dish.price}
                  </span>
                  <span className="text-xs font-semibold text-text-muted">
                    Serve 1 pessoa
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Scroll hint for mobile */}
      <p className="mt-4 text-center text-sm text-text-muted md:hidden">
        Arraste para ver mais pratos
      </p>
    </section>
  );
}
