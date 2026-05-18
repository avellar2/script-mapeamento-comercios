"use client";

import { motion } from "framer-motion";
import { Car, Droplets, Sparkles, Gauge, Star, Clock, Shield, Zap } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { LiquidGlass } from "@/components/demos/LiquidGlass";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#ef4444";
const phone = "5511999999006";
const name = "Auto Prime";

const services = [
  { icon: Droplets, title: "Lavagem Detalhada", desc: "Limpeza profunda de interior e exterior." },
  { icon: Sparkles, title: "Polimento", desc: "Correcao de pintura e protecao ceramica." },
  { icon: Gauge, title: "Martelinho", desc: "Remocao de amassados sem pintura." },
  { icon: Car, title: "Insulfilm", desc: "Peliculas, som e acessorios." },
];

export default function AutomotivaPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#fafafa" bgColor="#0a0a0a" whatsappLabel="Pedir orcamento">
      {/* Hero - Full width dark, car-centric */}
      <section className="relative min-h-[100dvh] flex items-end overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent z-10" />
        <div className="absolute inset-0">
          <div className="w-full h-full bg-gradient-to-br from-red-950/20 to-neutral-950" />
        </div>

        <div className="relative z-20 w-full max-w-7xl mx-auto px-5 py-20">
          <motion.div
            initial={{ opacity: 0, y: 60 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-red-500/10 border border-red-500/20 px-4 py-1.5 text-xs font-bold text-red-400 mb-6">
              <Zap size={12} /> Premium
            </div>

            <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-white leading-[0.9] tracking-tighter">
              Seu carro
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-500">
                merece brilho
              </span>
            </h1>

            <p className="mt-6 text-lg text-slate-400 leading-relaxed max-w-lg">
              Polimento, lavagem detalhada, estetica automotiva e martelinho de ouro.
              Transformacao completa com produtos de alta performance.
            </p>

            <div className="mt-8">
              <MagneticButton
                phone={phone}
                label="Pedir orcamento"
                businessName={name}
                accentColor={accent}
              />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Before/After comparison */}
      <section className="py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-red-500 mb-3 block">Resultados</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">Antes e depois</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              { title: "Polimento", before: "#262626", after: "#dc2626" },
              { title: "Higienizacao", before: "#262626", after: "#ef4444" },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2, duration: 0.6 }}
                className="relative rounded-2xl overflow-hidden"
              >
                <div className="grid grid-cols-2 h-64">
                  <div className="flex items-center justify-center" style={{ backgroundColor: item.before }}>
                    <span className="text-white/30 font-bold text-sm">ANTES</span>
                  </div>
                  <div className="flex items-center justify-center" style={{ backgroundColor: item.after }}>
                    <span className="text-white font-bold text-sm">DEPOIS</span>
                  </div>
                </div>
                <div className="absolute bottom-4 left-4 bg-black/80 backdrop-blur-sm rounded-full px-4 py-2 text-sm font-bold text-white">
                  {item.title}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Servicos */}
      <section className="py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-red-500 mb-3 block">Servicos</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">O que fazemos</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-5">
            {services.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                whileHover={{ scale: 1.02 }}
                className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 hover:border-red-500/20 transition-all duration-300"
              >
                <div className="w-14 h-14 rounded-xl bg-red-500/10 flex items-center justify-center mb-4 group-hover:bg-red-500/20 transition-colors">
                  <s.icon size={28} className="text-red-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{s.title}</h3>
                <p className="text-slate-400">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Depoimentos */}
      <section className="py-24 px-5 bg-neutral-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-red-500 mb-3 block">Clientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">Quem confia, volta</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Andre M.", text: "Meu carro saiu parecendo zero. O polimento removeu todos os riscos de lava-rapido." },
              { name: "Juliana R.", text: "Higienizacao completa do interior. Cheirinho de novo e couro hidratado." },
              { name: "Bruno S.", text: "Orcamento rapido pelo WhatsApp com fotos. Servico feito no mesmo dia." },
            ].map((t, i) => (
              <StaggerItem key={i}>
                <LiquidGlass className="p-6 h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className="text-slate-300 text-sm leading-relaxed mb-4">"{t.text}"</p>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">{t.name}</p>
                </LiquidGlass>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Seu carro merece{" "}
              <span className="text-red-500">estar impecavel</span>
            </h2>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Pedir orcamento"
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
