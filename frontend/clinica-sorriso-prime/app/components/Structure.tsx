"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Stethoscope, Scan, Armchair, Wind } from "lucide-react";

const features = [
  {
    icon: Stethoscope,
    label: "Consultório equipado",
  },
  {
    icon: Scan,
    label: "Raio-X digital",
  },
  {
    icon: Armchair,
    label: "Cadeiras ergonômicas",
  },
  {
    icon: Wind,
    label: "Ambiente climatizado",
  },
];

const images = [
  "https://images.unsplash.com/photo-1629909615184-74f495363b67?w=500&h=350&fit=crop&q=80",
  "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&h=300&fit=crop&q=80",
  "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&h=300&fit=crop&q=80",
  "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=500&h=350&fit=crop&q=80",
];

export default function Structure() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section className="py-20 md:py-32 bg-white" ref={ref}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="lg:col-span-5 flex flex-col gap-6"
          >
            <span className="text-sm font-semibold text-primary uppercase tracking-wider">Estrutura</span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-[1.15]">
              Um espaço pensado para seu conforto
            </h2>
            <p className="text-base md:text-lg text-muted leading-relaxed">
              Cada detalhe da nossa clínica foi projetado para que você se sinta acolhido. Desde a sala de espera até as cadeiras de atendimento, priorizamos seu bem-estar.
            </p>

            <div className="grid grid-cols-2 gap-3 pt-2">
              {features.map((f) => (
                <div key={f.label} className="flex items-center gap-2.5 p-3 rounded-xl bg-surface border border-border">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    <f.icon size={16} strokeWidth={1.5} />
                  </div>
                  <span className="text-sm font-medium text-slate-700">{f.label}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.1 }}
            className="lg:col-span-7 grid grid-cols-2 gap-3 md:gap-4"
          >
            <div className="col-span-2 relative rounded-[1.5rem] overflow-hidden aspect-[16/9] shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
              <img src={images[0]} alt="Recepção da clínica" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/20 to-transparent" />
            </div>
            <div className="relative rounded-[1.5rem] overflow-hidden aspect-[4/3] shadow-[0_12px_30px_-10px_rgba(0,0,0,0.08)]">
              <img src={images[1]} alt="Sala de atendimento" className="w-full h-full object-cover" />
            </div>
            <div className="relative rounded-[1.5rem] overflow-hidden aspect-[4/3] shadow-[0_12px_30px_-10px_rgba(0,0,0,0.08)]">
              <img src={images[2]} alt="Equipamento moderno" className="w-full h-full object-cover" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
