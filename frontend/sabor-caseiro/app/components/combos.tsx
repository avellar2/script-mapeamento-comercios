"use client";

import { motion } from "framer-motion";
import { Plus, Drop, Cookie, ArrowRight } from "@phosphor-icons/react";

const combos = [
  {
    id: 1,
    name: "Combo Executivo",
    desc: "Prato do dia + suco natural + sobremesa",
    original: "R$ 34,90",
    price: "R$ 29,90",
    image: "https://picsum.photos/seed/combo-exec-br/500/500",
  },
  {
    id: 2,
    name: "Combo Família",
    desc: "4 pratos + refrigerante 2L",
    original: "R$ 112,00",
    price: "R$ 99,00",
    image: "https://picsum.photos/seed/combo-fam-br/400/400",
  },
  {
    id: 3,
    name: "Combo Fitness",
    desc: "Prato light + suco detox",
    original: "R$ 32,90",
    price: "R$ 27,90",
    image: "https://picsum.photos/seed/combo-fit-br/400/400",
  },
  {
    id: 4,
    name: "Combo Almoço",
    desc: "Prato + sopa + café",
    original: "R$ 29,90",
    price: "R$ 24,90",
    image: "https://picsum.photos/seed/combo-alm-br/400/400",
  },
];

export function Combos() {
  return (
    <section className="relative w-full bg-cream py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-6 md:px-12 lg:px-20">
        <motion.div
          className="mb-12 flex flex-col items-center gap-3"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <p className="text-sm font-bold uppercase tracking-widest text-accent">
            Combos Especiais
          </p>
          <h2 className="text-center text-4xl font-black leading-[0.9] tracking-tight text-wood md:text-5xl">
            Mais vantagem no mesmo sabor.
          </h2>
        </motion.div>

        {/* Comandas de bar pinned on string */}
        <div className="relative flex flex-col gap-6 md:flex-row md:items-start md:justify-center">
          {/* String line */}
          <div className="absolute left-0 right-0 top-0 hidden h-[2px] bg-wood/30 md:block" />

          {combos.map((combo, i) => (
            <motion.div
              key={combo.id}
              className="group relative mx-auto w-full max-w-[300px] md:mx-0"
              initial={{ opacity: 0, y: 20, rotate: i % 2 === 0 ? -2 : 2 }}
              whileInView={{ opacity: 1, y: 0, rotate: i % 2 === 0 ? -2 : 2 }}
              viewport={{ once: true }}
              transition={{
                type: "spring",
                stiffness: 100,
                damping: 20,
                delay: i * 0.1,
              }}
              whileHover={{ rotate: 0, scale: 1.03 }}
            >
              {/* Pin */}
              <div className="absolute left-1/2 top-0 z-10 hidden h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full bg-red shadow-md md:block"
                style={{ boxShadow: "0 2px 4px rgba(0,0,0,0.3)" }}
              />

              {/* Comanda paper */}
              <div className="overflow-hidden rounded-lg bg-yellow/30 shadow-[0_4px_12px_rgba(93,64,55,0.15)]"
                style={{ background: "linear-gradient(to bottom, #FFF8E1 0%, #FFECB3 100%)" }}
              >
                {/* Torn edge top */}
                <div className="flex">
                  {Array.from({ length: 20 }).map((_, j) => (
                    <div
                      key={j}
                      className="h-3 w-[5%] bg-cream"
                      style={{
                        clipPath: j % 2 === 0 ? "polygon(0 0, 100% 100%, 100% 0)" : "polygon(0 0, 0 100%, 100% 0)",
                      }}
                    />
                  ))}
                </div>

                <div className="p-5">
                  <div className="relative h-40 w-full overflow-hidden rounded border-2 border-dashed border-wood/20">
                    <img
                      src={combo.image}
                      alt={combo.name}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                  </div>

                  <div className="mt-4 text-center">
                    <h3 className="text-xl font-black text-wood">
                      {combo.name}
                    </h3>
                    <p className="mt-1 text-sm text-text-secondary">
                      {combo.desc}
                    </p>
                    <div className="mt-3 flex items-center justify-center gap-3">
                      <span className="text-sm text-text-muted line-through">
                        {combo.original}
                      </span>
                      <span className="font-mono text-2xl font-bold text-red">
                        {combo.price}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Torn edge bottom */}
                <div className="flex">
                  {Array.from({ length: 20 }).map((_, j) => (
                    <div
                      key={j}
                      className="h-3 w-[5%] bg-cream"
                      style={{
                        clipPath: j % 2 === 0 ? "polygon(0 100%, 100% 0, 100% 100%)" : "polygon(0 0, 0 100%, 100% 100%)",
                      }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Extras */}
        <motion.div
          className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-text-secondary"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
        >
          <span className="flex items-center gap-2 rounded-full bg-surface px-4 py-2">
            <Plus size={16} weight="bold" className="text-accent" />
            Troca de acompanhamento grátis
          </span>
          <span className="flex items-center gap-2 rounded-full bg-surface px-4 py-2">
            <Drop size={16} weight="bold" className="text-accent" />
            Suco natural da estação
          </span>
          <span className="flex items-center gap-2 rounded-full bg-surface px-4 py-2">
            <Cookie size={16} weight="bold" className="text-accent" />
            Sobremesa caseira
          </span>
        </motion.div>
      </div>
    </section>
  );
}
