"use client";

import { motion } from "framer-motion";
import { Scissors, User, Sparkles, Star, Shield, Clock, Zap, MapPin } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { LiquidGlass } from "@/components/demos/LiquidGlass";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#d97706";
const phone = "5511999999010";
const name = "Barbearia Imperial";

const services = [
  { icon: Scissors, title: "Corte Masculino", desc: "Degrade, social, texturizado e moderno.", price: "R$ 45" },
  { icon: User, title: "Barba", desc: "Desenho de barba, navalha e hidratacao.", price: "R$ 35" },
  { icon: Sparkles, title: "Tratamentos", desc: "Hidratacao capilar e limpeza de pele.", price: "R$ 50" },
  { icon: Shield, title: "Combo", desc: "Corte + barba + sobrancelha.", price: "R$ 90" },
];

export default function BarbeariaPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#fafafa" bgColor="#0c0a09" whatsappLabel="Agendar corte">
      {/* Hero - Dark, urban, bold */}
      <section className="relative min-h-[100dvh] flex items-center overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_100%,_rgba(217,119,6,0.15),transparent)]" />
          <div className="absolute top-0 right-0 w-96 h-96 bg-amber-900/10 rounded-full blur-[120px]" />
        </div>

        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-amber-500/10 border border-amber-500/20 px-4 py-1.5 text-xs font-bold text-amber-400 mb-8">
                  <Zap size={12} /> Corte na regua
                </span>

                <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-white leading-[0.9] tracking-tighter">
                  Estilo que{" "}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-500 to-orange-400">
                    impressiona
                  </span>
                </h1>

                <p className="mt-6 text-lg text-slate-400 leading-relaxed max-w-md">
                  Cortes masculinos, barba, tratamentos e ambiente premium.
                  Agendamento pratico e atendimento de quem entende do assunto.
                </p>

                <div className="mt-8">
                  <MagneticButton
                    phone={phone}
                    label="Agendar corte"
                    businessName={name}
                    accentColor={accent}
                  />
                </div>
              </motion.div>
            </div>

            <div className="hidden lg:block">
              <motion.div
                initial={{ opacity: 0, x: 60 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 1, delay: 0.2 }}
                className="relative"
              >
                <div className="aspect-[3/4] rounded-3xl bg-gradient-to-br from-amber-950 to-neutral-900 flex items-center justify-center overflow-hidden">
                  <Scissors size={200} className="text-amber-800/20" strokeWidth={0.5} />
                </div>
                <motion.div
                  className="absolute -bottom-4 -left-4 bg-neutral-900 border border-amber-500/20 rounded-2xl p-5"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.6 }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center">
                      <Clock size={18} className="text-amber-500" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">Seg a Sab</div>
                      <div className="text-xs text-slate-500">9h as 20h</div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Servicos com precos */}
      <section className="py-24 px-5">
        <div className="max-w-5xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-amber-500 mb-3 block">Servicos</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">Tabela de precos</h2>
          </motion.div>

          <div className="space-y-3">
            {services.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                whileHover={{ x: 8 }}
                className="group flex items-center gap-6 p-6 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-amber-500/20 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                  <s.icon size={22} className="text-amber-500" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-white">{s.title}</h3>
                  <p className="text-sm text-slate-500">{s.desc}</p>
                </div>
                <div className="text-lg font-black text-amber-500">{s.price}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Depoimentos */}
      <section className="py-24 px-5 bg-neutral-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-amber-500 mb-3 block">Clientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">Quem passa aqui, volta</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Matheus R.", text: "Melhor corte da cidade. O degrade sai perfeito toda vez." },
              { name: "Lucas S.", text: "Ambiente premium, atendimento de verdade e cerveja gelada enquanto espero." },
              { name: "Gabriel T.", text: "Agendei pelo WhatsApp e cheguei na hora certa. Sem fila, sem espera." },
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
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-12">
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-amber-500 mb-3 block">Duvidas</span>
            <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            dark
            items={[
              { question: "Preciso agendar?", answer: "Sim. Trabalhamos apenas com agendamento para garantir atendimento exclusivo e sem espera." },
              { question: "Quanto tempo dura o corte?", answer: "Em media 45 minutos. Cortes mais elaborados podem levar ate 1h." },
              { question: "Aceita cartao?", answer: "Sim. Aceitamos cartoes de credito, debito e PIX." },
              { question: "Tem corte infantil?", answer: "Sim. Atendemos a partir dos 5 anos. Agende com antecedencia." },
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
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Seu estilo comeca com um{" "}
              <span className="text-amber-500">
                bom corte
              </span>
            </h2>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Agendar corte"
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
