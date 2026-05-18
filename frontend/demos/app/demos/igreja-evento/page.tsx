"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { Flame, Calendar, Mic, Music, Users, Heart, MapPin, Ticket, Star, Clock } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { Marquee } from "@/components/demos/Marquee";
import { LiquidGlass } from "@/components/demos/LiquidGlass";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#7c3aed";
const phone = "5511999999004";
const name = "Conferencia Avivados";

const speakers = ["Pr. Joao Silva", "Dra. Maria Oliveira", "Pr. Carlos Mendes", "Dra. Ana Costa", "Pr. Pedro Lima"];

const schedule = [
  { day: "Dia 1", time: "19h", title: "Abertura", desc: "Adoracao e palavra de lancamento" },
  { day: "Dia 2", time: "09h", title: "Manha", desc: "Palestras e workshops" },
  { day: "Dia 2", time: "19h", title: "Noite", desc: "Adoracao e ministeracao" },
  { day: "Dia 3", time: "09h", title: "Encerramento", desc: "Culto final e comissao" },
];

export default function IgrejaEventoPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]);

  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#f8fafc" bgColor="#020617" whatsappLabel="Fazer inscricao">
      {/* Hero - Full bleed with parallax */}
      <section ref={containerRef} className="relative min-h-[100dvh] flex items-center overflow-hidden">
        <motion.div className="absolute inset-0" style={{ y }}>
          <div className="absolute inset-0 bg-gradient-to-b from-violet-950/40 via-slate-950/80 to-slate-950" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_0%,_rgba(124,58,237,0.2),transparent)]" />
        </motion.div>

        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-violet-500/10 border border-violet-500/20 px-4 py-1.5 text-xs font-bold text-violet-400 mb-8">
              <Flame size={12} /> 15 a 17 de Maio de 2026
            </div>

            <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-white leading-[0.9] tracking-tight">
              Avivados
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-fuchsia-400">2026</span>
            </h1>

            <p className="mt-8 text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
              Tres dias de adoracao, palavra e comunhao. Uma experiencia que vai marcar a sua historia.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center">
              <MagneticButton
                phone={phone}
                label="Fazer inscricao"
                businessName={name}
                accentColor={accent}
              />
              <span className="text-sm text-slate-500">Vagas limitadas por lote</span>
            </div>

            <div className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto">
              {[
                { value: "3", label: "Dias" },
                { value: "+", label: "2000 pessoas" },
                { value: "5", label: "Preletores" },
              ].map((stat, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + i * 0.1, duration: 0.6 }}
                  className="text-center"
                >
                  <div className="text-3xl md:text-4xl font-black text-white">{stat.value}</div>
                  <div className="text-xs text-slate-500 mt-1">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Marquee de preletores */}
      <Marquee speed={20} dark>
        {speakers.map((s, i) => (
          <span key={i} className="inline-flex items-center gap-3 text-lg text-slate-500">
            <Mic size={18} className="text-violet-500" />
            {s}
          </span>
        ))}
      </Marquee>

      {/* Programacao */}
      <section className="py-24 px-5">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16 text-center">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-violet-400 mb-3 block">Programacao</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">O que esperar</h2>
          </motion.div>

          <div className="space-y-4">
            {schedule.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
              >
                <LiquidGlass className="p-6 flex items-center gap-6">
                  <div className="text-center flex-shrink-0 w-16">
                    <div className="text-xs text-slate-500">{item.day}</div>
                    <div className="text-xl font-black text-white">{item.time}</div>
                  </div>
                  <div className="flex-1">
                    <div className="text-lg font-bold text-white">{item.title}</div>
                    <div className="text-sm text-slate-400">{item.desc}</div>
                  </div>
                  <Clock size={20} className="text-violet-500 flex-shrink-0" />
                </LiquidGlass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Depoimentos */}
      <section className="py-24 px-5 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16 text-center">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-violet-400 mb-3 block">Quem viveu</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">Depoimentos do ano passado</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Lucas L.", text: "Vim desanimado e voltei renovado. A palavra da ultima noite mudou minha trajetoria." },
              { name: "Mariana S.", text: "A adoracao foi surreal. Senti a presenca de Deus de um jeito que nunca tinha sentido." },
              { name: "Roberto K.", text: "Fiz amizades que duram ate hoje. A comunhao do Avivados e diferente de tudo." },
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

      {/* FAQ */}
      <section className="py-24 px-5">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-12 text-center">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-violet-400 mb-3 block">Duvidas</span>
            <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            dark
            items={[
              { question: "Qual o valor do ingresso?", answer: "Os ingressos sao comercializados por lote. Consulte o valor atual pelo WhatsApp." },
              { question: "Posso levar criancas?", answer: "Sim. Temos espaco kids com monitoras capacitadas durante todo o evento." },
              { question: "Tem estacionamento?", answer: "Sim. Estacionamento amplo e seguro com manobrista incluso no ingresso." },
              { question: "Como funciona a inscricao?", answer: "Envie uma mensagem pelo WhatsApp com seu nome completo e escolha a forma de pagamento." },
            ]}
          />
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-32 px-5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Sua presenca faz{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-fuchsia-400">
                toda a diferenca
              </span>
            </h2>
            <p className="mt-6 text-lg text-slate-400 max-w-xl mx-auto">
              Nao espacar esgotar. Garanta sua vaga na Conferencia Avivados 2026.
            </p>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Fazer inscricao"
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
