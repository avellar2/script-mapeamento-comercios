"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight } from "@phosphor-icons/react";

const menuItems = [
  {
    category: "Carnes",
    items: [
      { name: "Strogonoff de Frango", desc: "Arroz, batata palha, molho cremoso", price: "R$ 24,90" },
      { name: "Bife Acebolado", desc: "Contra-filé, cebola, purê rústico", price: "R$ 28,50" },
      { name: "Frango à Parmegiana", desc: "Arroz, batata frita, salada", price: "R$ 26,90" },
      { name: "Picadinho de Carne", desc: "Arroz, feijão tropeiro, couve", price: "R$ 27,90" },
    ],
  },
  {
    category: "Peixes",
    items: [
      { name: "Filé de Tilápia", desc: "Arroz integral, legumes salteados", price: "R$ 27,90" },
      { name: "Salmão Grelhado", desc: "Purê de batata-doce, brócolis", price: "R$ 32,00" },
    ],
  },
  {
    category: "Executivos",
    items: [
      { name: "Feijoada Completa", desc: "Arroz, couve, farofa, laranja", price: "R$ 31,00" },
      { name: "Lasanha Bolonhesa", desc: "Salada verde, pão de alho", price: "R$ 25,90" },
      { name: "Escondidinho de Carne", desc: "Mandioca, queijo gratinado", price: "R$ 24,90" },
    ],
  },
];

export function Menu() {
  const [activeCategory, setActiveCategory] = useState(0);

  return (
    <section className="relative w-full bg-surface py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-6 md:px-12 lg:px-20">
        <motion.div
          className="mb-10 flex flex-col items-center gap-3"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <p className="text-sm font-bold uppercase tracking-widest text-accent">
            Cardápio Completo
          </p>
          <h2 className="text-center text-4xl font-black leading-[0.9] tracking-tight text-wood md:text-5xl">
            Tudo que a gente faz bem.
          </h2>
        </motion.div>

        {/* Notebook style cardápio */}
        <div className="mx-auto max-w-[700px] overflow-hidden rounded-lg shadow-[0_12px_40px_rgba(93,64,55,0.2)]">
          {/* Spiral binding top */}
          <div className="flex items-center justify-center gap-3 bg-wood py-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="h-4 w-4 rounded-full border-2 border-cream bg-surface shadow-sm" />
            ))}
          </div>

          {/* Paper background */}
          <div className="relative bg-[#FFF8E1] p-6 md:p-8"
            style={{ backgroundImage: "repeating-linear-gradient(transparent, transparent 31px, #e0d6c2 31px, #e0d6c2 32px)" }}
          >
            {/* Category tabs */}
            <div className="mb-6 flex gap-2">
              {menuItems.map((cat, i) => (
                <button
                  key={cat.category}
                  onClick={() => setActiveCategory(i)}
                  className={`rounded-full px-4 py-2 text-sm font-bold transition-all ${
                    activeCategory === i
                      ? "bg-red text-white shadow-md"
                      : "bg-surface text-wood hover:bg-accent/10"
                  }`}
                >
                  {cat.category}
                </button>
              ))}
            </div>

            {/* Menu items */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeCategory}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                className="flex flex-col"
              >
                {menuItems[activeCategory].items.map((item, ii) => (
                  <div
                    key={item.name}
                    className="group flex items-center justify-between border-b border-dashed border-wood/20 py-4"
                  >
                    <div className="flex flex-col">
                      <span className="text-base font-bold text-wood group-hover:text-red">
                        {item.name}
                      </span>
                      <span className="text-sm text-text-muted">
                        {item.desc}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-lg font-bold text-accent">
                        {item.price}
                      </span>
                      <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-wood/20 text-wood transition-all group-hover:border-red group-hover:bg-red group-hover:text-white"
                      >
                        <ArrowRight size={14} weight="bold" />
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            </AnimatePresence>

            {/* Handwritten note at bottom */}
            <div className="mt-6 flex items-start gap-3 rounded-lg bg-yellow/20 p-4">
              <div className="mt-1 h-4 w-4 shrink-0 rounded-full bg-accent" />
              <p className="text-sm italic leading-relaxed text-text-secondary">
                "A comida muda todo dia conforme o humor do fogão. Pergunta no WhatsApp o que tem hoje!"
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
