"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useRef } from "react";
import {
  Zap,
  Smartphone,
  Laptop,
  Snowflake,
  Plug,
  Clock,
  Shield,
  Wrench,
  MapPin,
  ChevronRight,
  Star,
  Phone,
  Wifi,
} from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { TiltCard } from "@/components/demos/TiltCard";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { Marquee } from "@/components/demos/Marquee";
import { LiquidGlass } from "@/components/demos/LiquidGlass";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#06b6d4";
const phone = "5511999999001";
const name = "Resolve Ja";

const services = [
  { icon: Smartphone, title: "Celular e Tablet", desc: "Troca de tela, bateria, conector e reparo de placa." },
  { icon: Laptop, title: "Notebook", desc: "Formatacao, upgrade SSD, limpeza e remocao de virus." },
  { icon: Snowflake, title: "Ar-Condicionado", desc: "Limpeza, instalacao, manutencao e carga de gas." },
  { icon: Plug, title: "Eletricista", desc: "Instalacoes, reparos, curto-circuito e adequacao." },
];

const stats = [
  { value: "15min", label: "Tempo medio de resposta" },
  { value: "2.400+", label: "Consertos realizados" },
  { value: "98%", label: "Clientes satisfeitos" },
  { value: "90d", label: "Garantia nos servicos" },
];

export default function AssistenciaTecnicaPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 50, damping: 20 });
  const bgX = useTransform(springX, [-500, 500], [-30, 30]);
  const bgY = useTransform(springY, [-500, 500], [-30, 30]);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!heroRef.current) return;
    const rect = heroRef.current.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left - rect.width / 2);
    mouseY.set(e.clientY - rect.top - rect.height / 2);
  };

  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#f8fafc" bgColor="#030712" whatsappLabel="Pedir orçamento">
      {/* Hero - Split Screen com parallax */}
      <section
        ref={heroRef}
        onMouseMove={handleMouseMove}
        className="relative min-h-[100dvh] flex items-center overflow-hidden"
      >
        <motion.div
          className="absolute inset-0 opacity-30"
          style={{ x: bgX, y: bgY }}
        >
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_70%_40%,_rgba(6,182,212,0.15),transparent)]" />
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-cyan-500/[0.07] rounded-full blur-[100px]" />
          <div className="absolute bottom-1/4 left-1/4 w-64 h-64 bg-blue-500/[0.05] rounded-full blur-[80px]" />
        </motion.div>

        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, x: -40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
              >
                <div className="inline-flex items-center gap-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 px-4 py-1.5 text-xs font-bold text-cyan-400 mb-6">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    <Wifi size={12} />
                  </motion.div>
                  Atendimento online agora
                </div>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-white leading-[0.95] tracking-tight">
                  Tecnico na sua porta em{" "}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                    60 minutos
                  </span>
                </h1>

                <p className="mt-6 text-lg text-slate-400 leading-relaxed max-w-md">
                  Conserto de celular, notebook, ar-condicionado e eletricista.
                  Orcamento honesto e garantia real no servico.
                </p>

                <div className="mt-8 flex flex-col sm:flex-row gap-4">
                  <MagneticButton
                    phone={phone}
                    label="Pedir orçamento agora"
                    businessName={name}
                    accentColor={accent}
                  />
                  <span className="flex items-center gap-2 text-sm text-slate-500">
                    <motion.div
                      className="w-2 h-2 rounded-full bg-green-500"
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                    />
                    Tecnico disponivel agora
                  </span>
                </div>
              </motion.div>
            </div>

            <div className="hidden md:block">
              <LiquidGlass className="p-8">
                <div className="grid grid-cols-2 gap-4">
                  {stats.map((stat, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 20, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ delay: 0.4 + i * 0.1, duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
                      className="text-center p-4"
                    >
                      <div className="text-3xl font-black text-white">{stat.value}</div>
                      <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
                    </motion.div>
                  ))}
                </div>
              </LiquidGlass>
            </div>
          </div>
        </div>
      </section>

      {/* Marquee de servicos */}
      <Marquee speed={25} dark>
        {services.map((s, i) => (
          <span key={i} className="inline-flex items-center gap-2 text-sm text-slate-500">
            <s.icon size={16} className="text-cyan-500" />
            {s.title}
          </span>
        ))}
      </Marquee>

      {/* Servicos com Tilt Cards */}
      <section className="relative py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-cyan-500 mb-3 block">Servicos</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">Consertamos tudo que liga</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-5">
            {services.map((s, i) => (
              <TiltCard
                key={i}
                icon={s.icon}
                title={s.title}
                description={s.desc}
                accentColor={accent}
                delay={i * 0.1}
                dark
              />
            ))}
          </div>
        </div>
      </section>

      {/* Prova Social - Glass panel */}
      <section className="relative py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6">
            <StaggerContainer className="md:col-span-2 grid gap-6">
              {[
                { name: "Marcelo R.", text: "Meu celular caiu na agua e pensei que tinha perdido. Em 2h estava funcionando de novo.", rating: 5 },
                { name: "Fernanda L.", text: "Orcamento pelo WhatsApp e o tecnico chegou no mesmo dia. Super pratico.", rating: 5 },
              ].map((t, i) => (
                <StaggerItem key={i}>
                  <LiquidGlass className="p-6">
                    <div className="flex gap-1 mb-3">
                      {Array.from({ length: t.rating }).map((_, j) => (
                        <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                      ))}
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed mb-4">"{t.text}"</p>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">{t.name}</p>
                  </LiquidGlass>
                </StaggerItem>
              ))}
            </StaggerContainer>

            <StaggerContainer className="space-y-6">
              <StaggerItem>
                <LiquidGlass className="p-6 text-center">
                  <Clock size={32} className="mx-auto mb-3 text-cyan-500" />
                  <div className="text-3xl font-black text-white">1h</div>
                  <div className="text-xs text-slate-400 mt-1">Tempo medio de chegada</div>
                </LiquidGlass>
              </StaggerItem>
              <StaggerItem>
                <LiquidGlass className="p-6 text-center">
                  <Shield size={32} className="mx-auto mb-3 text-cyan-500" />
                  <div className="text-3xl font-black text-white">90d</div>
                  <div className="text-xs text-slate-400 mt-1">Garantia em todos os servicos</div>
                </LiquidGlass>
              </StaggerItem>
            </StaggerContainer>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="relative py-24 px-5">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-12">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-cyan-500 mb-3 block">Duvidas</span>
            <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            dark
            items={[
              { question: "Quanto tempo demora o conserto?", answer: "A maioria dos consertos e feita em ate 2h. Servicos mais complexos podem levar ate 24h." },
              { question: "Voces dao garantia?", answer: "Sim. Todos os servicos tem garantia de 90 dias. Pecas novas com nota fiscal." },
              { question: "Atendem a domicilio?", answer: "Sim. Atendemos a domicilio em toda a Grande Sao Paulo. Deslocamento sob consulta." },
              { question: "Como funciona o orcamento?", answer: "Voce descreve o problema pelo WhatsApp, enviamos um valor estimado e so iniciamos com a sua aprovacao." },
            ]}
          />
        </div>
      </section>

      {/* CTA Final */}
      <section className="relative py-32 px-5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Nao deixe o problema{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                virar dor de cabeca
              </span>
            </h2>
            <p className="mt-6 text-lg text-slate-400 max-w-xl mx-auto">
              Orcamento rapido, atendimento honesto e garantia real no servico.
            </p>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Pedir orçamento agora"
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
