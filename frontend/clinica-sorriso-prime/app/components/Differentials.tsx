"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Heart, Home, GraduationCap, Monitor, CalendarCheck } from "lucide-react";

const differentials = [
  {
    icon: Heart,
    title: "Atendimento humanizado",
    description: "Cada paciente é ouvido, respeitado e tratado com atenção individual desde o primeiro contato.",
  },
  {
    icon: Home,
    title: "Ambiente confortável",
    description: "Espaço pensado para seu bem-estar, com aroma, música e uma atmosfera que reduz a tensão.",
  },
  {
    icon: GraduationCap,
    title: "Profissionais qualificados",
    description: "Equipe com formação contínua e experiência prática em procedimentos modernos.",
  },
  {
    icon: Monitor,
    title: "Tecnologia no atendimento",
    description: "Equipamento digital, radiografia computadorizada e sistemas de planejamento 3D.",
  },
  {
    icon: CalendarCheck,
    title: "Facilidade para agendar",
    description: "Agendamento direto pelo WhatsApp com resposta rápida e horários flexíveis.",
  },
];

export default function Differentials() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="diferenciais" className="py-20 md:py-32 bg-surface" ref={ref}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="lg:sticky lg:top-28"
          >
            <span className="text-sm font-semibold text-primary uppercase tracking-wider">Diferenciais</span>
            <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-[1.15]">
              Por que escolher a{" "}
              <span className="text-primary">Sorriso Prime</span>?
            </h2>
            <p className="mt-5 text-base md:text-lg text-muted leading-relaxed max-w-md">
              Acreditamos que ir ao dentista pode ser uma experiência leve. Nosso diferencial está em cada detalhe.
            </p>

            <div className="hidden lg:block mt-10 relative rounded-[2rem] overflow-hidden aspect-[4/3] shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
              <img
                src="https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=600&h=500&fit=crop&q=80"
                alt="Atendimento odontológico humanizado"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/30 to-transparent" />
              <div className="absolute bottom-6 left-6 right-6">
                <p className="text-white font-semibold text-lg">Sua tranquilidade em primeiro lugar</p>
              </div>
            </div>
          </motion.div>

          <div className="flex flex-col gap-4">
            {differentials.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ type: "spring", stiffness: 100, damping: 20, delay: i * 0.1 }}
                className="group flex gap-5 p-6 md:p-7 bg-white rounded-[1.5rem] border border-border hover:border-primary/20 hover:shadow-[0_12px_30px_-10px_rgba(0,0,0,0.06)] transition-all duration-300"
              >
                <div className="shrink-0 w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary group-hover:text-white text-primary transition-colors"
                >
                  <item.icon size={22} strokeWidth={1.5} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-1.5">{item.title}</h3>
                  <p className="text-sm text-muted leading-relaxed">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
