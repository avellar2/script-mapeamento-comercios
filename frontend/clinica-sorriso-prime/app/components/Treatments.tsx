"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Sparkles, Shield, Smile, AlignCenter, Bone, Wrench, Target, ArrowRight } from "lucide-react";

const treatments = [
  {
    icon: Target,
    title: "Avaliação Odontológica",
    description: "Exame completo para entender sua saúde bucal e definir o melhor plano de cuidados.",
    color: "bg-primary/10 text-primary",
  },
  {
    icon: Sparkles,
    title: "Limpeza",
    description: "Remoção de tártaro e placa bacteriana com cuidado e tecnologia ultrassônica.",
    color: "bg-accent/10 text-accent",
  },
  {
    icon: Smile,
    title: "Clareamento",
    description: "Procedimento estético seguro para revitalizar o brilho natural dos seus dentes.",
    color: "bg-primary/10 text-primary",
  },
  {
    icon: AlignCenter,
    title: "Ortodontia",
    description: "Alinhadores modernos e aparelhos para uma oclusão saudável e estética.",
    color: "bg-accent/10 text-accent",
  },
  {
    icon: Bone,
    title: "Implantes",
    description: "Reposição de dentes ausentes com bioestratégia e materiais de alta performance.",
    color: "bg-primary/10 text-primary",
  },
  {
    icon: Wrench,
    title: "Restaurações",
    description: "Reconstrução estética e funcional com resinas de última geração.",
    color: "bg-accent/10 text-accent",
  },
  {
    icon: Shield,
    title: "Tratamento de Canal",
    description: "Endodontia moderna com conforto, preservando seu dente natural sempre que possível.",
    color: "bg-primary/10 text-primary",
  },
];

function TreatmentCard({ treatment, index }: { treatment: typeof treatments[0]; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ type: "spring", stiffness: 100, damping: 20, delay: index * 0.08 }}
      className="group relative flex flex-col gap-4 p-6 md:p-8 bg-white rounded-[1.5rem] border border-border hover:border-primary/20 hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.06)] transition-all duration-300"
    >
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${treatment.color}`}>
        <treatment.icon size={22} strokeWidth={1.5} />
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-slate-900 mb-2">{treatment.title}</h3>
        <p className="text-sm text-muted leading-relaxed">{treatment.description}</p>
      </div>
      <div className="flex items-center gap-1 text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
        <span>Saiba mais</span>
        <ArrowRight size={14} />
      </div>
    </motion.div>
  );
}

export default function Treatments() {
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });

  return (
    <section id="tratamentos" className="py-20 md:py-32 bg-white" ref={sectionRef}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="max-w-2xl mb-12 md:mb-16"
        >
          <span className="text-sm font-semibold text-primary uppercase tracking-wider">Tratamentos</span>
          <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900">
            Cuidamos de cada detalhe do seu sorriso
          </h2>
          <p className="mt-4 text-base md:text-lg text-muted leading-relaxed">
            Oferecemos soluções completas em odontologia, desde prevenção até reabilitação oral.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {treatments.map((treatment, i) => (
            <TreatmentCard key={treatment.title} treatment={treatment} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
