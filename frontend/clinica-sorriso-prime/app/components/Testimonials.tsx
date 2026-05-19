"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Star, Quote } from "lucide-react";

const testimonials = [
  {
    name: "Mariana Goulart",
    role: "Paciente desde 2022",
    text: "Sempre tive medo de dentista. Aqui pela primeira vez me senti ouvida e cuidada. O atendimento é delicado e o resultado do meu tratamento superou minhas expectativas.",
    rating: 5,
    image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&q=80",
  },
  {
    name: "Fernando Lopes",
    role: "Paciente desde 2023",
    text: "Fiz implante e o processo foi muito mais tranquilo do que imaginei. A equipe explicou cada etapa e me deu segurança do início ao fim.",
    rating: 5,
    image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&q=80",
  },
  {
    name: "Ana Carolina Dias",
    role: "Paciente desde 2021",
    text: "Levei minha mãe de 68 anos para avaliação. A paciência da Dra. Helena e a forma como explicou tudo para ela foi tocante. Encontramos um lugar de confiança.",
    rating: 5,
    image: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop&q=80",
  },
];

export default function Testimonials() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="depoimentos" className="py-20 md:py-32 bg-surface" ref={ref}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="text-center max-w-2xl mx-auto mb-12 md:mb-16"
        >
          <span className="text-sm font-semibold text-primary uppercase tracking-wider">Depoimentos</span>
          <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900">
            O que nossos pacientes dizem
          </h2>
          <p className="mt-4 text-base md:text-lg text-muted leading-relaxed">
            Cada sorriso atendido é uma história de confiança construída com cuidado.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: "spring", stiffness: 100, damping: 20, delay: i * 0.12 }}
              className="relative flex flex-col gap-5 p-6 md:p-8 bg-white rounded-[1.5rem] border border-border"
            >
              <div className="absolute top-6 right-6 text-primary/10">
                <Quote size={40} fill="currentColor" />
              </div>

              <div className="flex gap-1">
                {Array.from({ length: t.rating }).map((_, r) => (
                  <Star key={r} size={16} fill="currentColor" className="text-amber-400" />
                ))}
              </div>

              <p className="text-base text-slate-700 leading-relaxed flex-1">"{t.text}" </p>

              <div className="flex items-center gap-3 pt-2 border-t border-border">
                <img
                  src={t.image}
                  alt={t.name}
                  className="w-10 h-10 rounded-full object-cover"
                />
                <div>
                  <p className="text-sm font-semibold text-slate-900">{t.name}</p>
                  <p className="text-xs text-muted">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
