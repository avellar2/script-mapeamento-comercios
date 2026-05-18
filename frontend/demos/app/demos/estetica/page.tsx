"use client";

import { motion } from "framer-motion";
import { Sparkles, Eye, Heart, Sun, Star, MapPin, Clock, Phone } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { LiquidGlass } from "@/components/demos/LiquidGlass";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#d946ef";
const phone = "5511999999009";
const name = "Studio Bella Face";

const services = [
  { icon: Eye, title: "Cilios e Sobrancelha", desc: "Extensao de cilios, brow lamination e henna.", time: "1-2h" },
  { icon: Sparkles, title: "Limpeza de Pele", desc: "Limpeza profunda, peeling e hidratacao.", time: "1h" },
  { icon: Sun, title: "Depilacao", desc: "Cera quente e depilacao a laser.", time: "30-60min" },
  { icon: Heart, title: "Manicure", desc: "Esmaltacao tradicional, em gel e nail art.", time: "1h" },
];

export default function EsteticaPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#701a75" bgColor="#fdf4ff" whatsappLabel="Agendar agora">
      {/* Hero - Feminine, elegant, premium */}
      <section className="relative min-h-[100dvh] flex items-center">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-fuchsia-50 via-white to-pink-50" />
        <div className="absolute top-20 right-20 w-64 h-64 bg-fuchsia-200/20 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-20 w-48 h-48 bg-pink-200/20 rounded-full blur-3xl" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-5">
              <motion.div
                initial={{ opacity: 0, x: -40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-fuchsia-50 border border-fuchsia-200 px-4 py-1.5 text-xs font-semibold text-fuchsia-700 mb-8">
                  <Sparkles size={12} /> Beleza e bem-estar
                </span>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-fuchsia-950 leading-[0.95] tracking-tight">
                  Seu momento de{" "}
                  <span className="text-fuchsia-600">
                    cuidado
                  </span>
                </h1>

                <p className="mt-8 text-lg text-fuchsia-900/70 leading-relaxed max-w-md">
                  Manicure, cilios, sobrancelha, limpeza de pele, depilacao e estetica facial.
                  Atendimento exclusivo em ambiente acolhedor.
                </p>

                <div className="mt-10">
                  <MagneticButton
                    phone={phone}
                    label="Agendar agora"
                    businessName={name}
                    accentColor={accent}
                  />
                </div>
              </motion.div>
            </div>

            <div className="lg:col-span-7">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 1, delay: 0.2 }}
                className="relative"
              >
                <div className="grid grid-cols-3 gap-3">
                  <motion.div
                    className="aspect-[3/4] rounded-3xl bg-gradient-to-br from-fuchsia-100 to-pink-100"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
                  >
                    <div className="w-full h-full flex items-center justify-center">
                      <Eye size={60} className="text-fuchsia-300" strokeWidth={1} />
                    </div>
                  </motion.div>
                  <motion.div
                    className="aspect-[3/4] rounded-3xl bg-gradient-to-br from-pink-100 to-rose-100 mt-8"
                    animate={{ y: [0, 8, 0] }}
                    transition={{ repeat: Infinity, duration: 5, ease: "easeInOut", delay: 1.5 }}
                  >
                    <div className="w-full h-full flex items-center justify-center">
                      <Sparkles size={60} className="text-pink-300" strokeWidth={1} />
                    </div>
                  </motion.div>
                  <motion.div
                    className="aspect-[3/4] rounded-3xl bg-gradient-to-br from-rose-100 to-fuchsia-100"
                    animate={{ y: [0, -6, 0] }}
                    transition={{ repeat: Infinity, duration: 5, ease: "easeInOut", delay: 3 }}
                  >
                    <div className="w-full h-full flex items-center justify-center">
                      <Heart size={60} className="text-rose-300" strokeWidth={1} />
                    </div>
                  </motion.div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Servicos */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-fuchsia-600 mb-3 block">Servicos</span>
            <h2 className="text-3xl md:text-5xl font-black text-fuchsia-950 tracking-tight">Cuidamos de voce</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-5">
            {services.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                whileHover={{ y: -4 }}
                className="group flex gap-6 p-6 rounded-2xl border border-fuchsia-100 hover:border-fuchsia-200 hover:shadow-lg transition-all duration-300 bg-white"
              >
                <div className="w-14 h-14 rounded-2xl bg-fuchsia-50 flex items-center justify-center flex-shrink-0 group-hover:bg-fuchsia-100 transition-colors">
                  <s.icon size={24} className="text-fuchsia-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-lg font-bold text-fuchsia-950">{s.title}</h3>
                    <span className="text-xs text-fuchsia-500 font-medium">{s.time}</span>
                  </div>
                  <p className="text-fuchsia-900/60 text-sm">{s.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Depoimentos */}
      <section className="py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-fuchsia-600 mb-3 block">Clientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-fuchsia-950 tracking-tight">Quem cuida, recomenda</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Renata S.", text: "Minha sobrancelha nunca esteve tao perfeita. Atendimento delicado e ambiente lindo." },
              { name: "Camila P.", text: "Cilios duram semanas e ficam naturais. Melhor investimento da minha rotina." },
              { name: "Fernanda L.", text: "Agendamento facil pelo WhatsApp e o resultado sempre me surpreende." },
            ].map((t, i) => (
              <StaggerItem key={i}>
                <div className="bg-white rounded-2xl p-6 border border-fuchsia-100 shadow-sm h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className="text-fuchsia-900/70 text-sm leading-relaxed mb-4">"{t.text}"</p>
                  <p className="text-xs font-bold text-fuchsia-950 uppercase tracking-wide">{t.name}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-5 bg-fuchsia-950">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Voce merece um momento{" "}
              <span className="text-fuchsia-400">
                so seu
              </span>
            </h2>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Agendar agora"
                businessName={name}
                accentColor={accent}
              />
            </div>
          </motion.div>
        </div>
      </section>
    </DemoLayout>
  );
}
