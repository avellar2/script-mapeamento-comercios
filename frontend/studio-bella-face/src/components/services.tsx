"use client";

import { motion } from "framer-motion";
import { staggerContainer, fadeInUp, scaleIn } from "./motion-variants";

const services = [
  {
    title: "Manicure",
    desc: "Esmaltação em gel, alongamento de fibra e cuidados completos para unhas impecáveis.",
    image: "https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=800&q=80",
    span: "md:col-span-2 md:row-span-2",
    aspect: "aspect-[4/3] md:aspect-auto",
  },
  {
    title: "Designer de Sobrancelhas",
    desc: "Design com henna, micropigmentação e harmonização facial personalizada.",
    image: "https://images.unsplash.com/photo-1522337660859-02fbefca4708?auto=format&fit=crop&w=600&q=80",
    span: "md:col-span-1 md:row-span-1",
    aspect: "aspect-[3/4]",
  },
  {
    title: "Cílios",
    desc: "Extensão fio a fio, volume russo e volume brasileiro com durabilidade excepcional.",
    image: "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=600&q=80",
    span: "md:col-span-1 md:row-span-1",
    aspect: "aspect-[3/4]",
  },
  {
    title: "Limpeza de Pele",
    desc: "Protocolos personalizados com extração, peeling e hidratação profunda.",
    image: "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=800&q=80",
    span: "md:col-span-2 md:row-span-2",
    aspect: "aspect-[4/3] md:aspect-auto",
  },
  {
    title: "Depilação",
    desc: "Cera quente, fria e linha para todos os tipos de pele. Higiene e conforto absolutos.",
    image: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
    span: "md:col-span-2 md:row-span-1",
    aspect: "aspect-[16/9]",
  },
  {
    title: "Estética Facial",
    desc: "Tratamentos rejuvenescedores com radiofrequência, ledterapia e dermaplaning.",
    image: "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?auto=format&fit=crop&w=600&q=80",
    span: "md:col-span-1 md:row-span-1",
    aspect: "aspect-[3/4]",
  },
];

export function Services() {
  return (
    <section className="relative w-full px-6 py-32 md:px-12 lg:px-20">
      <div className="mx-auto max-w-[1400px]">
        <motion.div
          className="mb-16 flex flex-col items-start gap-4"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.p
            variants={fadeInUp}
            className="text-sm font-medium uppercase tracking-widest text-accent"
          >
            Nossos Serviços
          </motion.p>
          <motion.h2
            variants={fadeInUp}
            className="max-w-[20ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl"
          >
            Tudo para sua beleza em um só lugar.
          </motion.h2>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 gap-4 md:grid-cols-3 md:auto-rows-[280px]"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          variants={staggerContainer}
        >
          {services.map((s) => (
            <motion.div
              key={s.title}
              className={`group relative overflow-hidden rounded-[1.5rem] ${s.span} ${s.aspect}`}
              variants={scaleIn}
              whileHover={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 200, damping: 25 }}
            >
              <img
                src={s.image}
                alt={s.title}
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
              <div className="absolute bottom-0 left-0 p-6 md:p-8">
                <h3 className="text-xl font-semibold text-white md:text-2xl">
                  {s.title}
                </h3>
                <p className="mt-1 max-w-[32ch] text-sm leading-relaxed text-white/80">
                  {s.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
