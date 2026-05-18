"use client";

import { motion } from "framer-motion";
import { GraduationCap, BookOpen, Calculator, Languages, Monitor, Users, Star, Clock, ArrowRight, Check } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#d97706";
const phone = "5511999999007";
const name = "Aprender Mais";

const courses = [
  { icon: Calculator, title: "Reforco Escolar", desc: "Matematica, portugues, ciencias e todas as disciplinas.", duration: "1h/aula", students: "+500" },
  { icon: Languages, title: "Ingles", desc: "Conversacao, gramatica e preparacao para provas.", duration: "1h/aula", students: "+300" },
  { icon: Monitor, title: "Informatica", desc: "Do basico ao avancado. Windows, Office e programacao.", duration: "1.5h/aula", students: "+200" },
  { icon: BookOpen, title: "Cursos Livres", desc: "Redacao, vestibular e desenvolvimento pessoal.", duration: "2h/aula", students: "+150" },
];

const timeline = [
  { step: "01", title: "Avaliacao", desc: "Avaliamos o nivel do aluno" },
  { step: "02", title: "Plano", desc: "Criamos um plano personalizado" },
  { step: "03", title: "Aulas", desc: "Aulas com metodologia propria" },
  { step: "04", title: "Resultado", desc: "Acompanhamento de progresso" },
];

export default function CursosPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#1e293b" bgColor="#fffbeb" whatsappLabel="Falar no WhatsApp">
      {/* Hero - Warm, friendly, split */}
      <section className="relative min-h-[100dvh] flex items-center">
        <div className="absolute top-0 right-0 w-[50%] h-full bg-gradient-to-l from-amber-50 to-transparent" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-amber-50 border border-amber-200 px-4 py-1.5 text-xs font-semibold text-amber-700 mb-8">
                  <GraduationCap size={12} /> Aulas presenciais e online
                </span>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-slate-900 leading-[0.95] tracking-tight">
                  Aprender faz{" "}
                  <span className="text-amber-600">
                    diferenca
                  </span>
                </h1>

                <p className="mt-8 text-lg text-slate-500 leading-relaxed max-w-lg">
                  Reforco escolar, aulas particulares, ingles, informatica e cursos livres.
                  Metodologia que conecta com o aluno e gera resultados.
                </p>

                <div className="mt-10">
                  <MagneticButton
                    phone={phone}
                    label="Falar no WhatsApp"
                    businessName={name}
                    accentColor={accent}
                  />
                </div>

                <div className="mt-12 flex gap-8">
                  {[
                    { value: "+", label: "1000 alunos" },
                    { value: "98%", label: "Aprovacao" },
                    { value: "15+", label: "Anos" },
                  ].map((stat, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 + i * 0.1, duration: 0.6 }}
                    >
                      <div className="text-3xl font-black text-slate-900">{stat.value}</div>
                      <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>

            <div className="hidden lg:block">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 1, delay: 0.2 }}
                className="relative"
              >
                <div className="aspect-square rounded-[2.5rem] bg-gradient-to-br from-amber-100 to-orange-50 flex items-center justify-center">
                  <GraduationCap size={160} className="text-amber-200" strokeWidth={1} />
                </div>
                <motion.div
                  className="absolute -bottom-4 -right-4 bg-white rounded-2xl shadow-xl p-5 border border-amber-100"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.6 }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                      <Check size={20} className="text-green-600" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Aula experimental</div>
                      <div className="text-xs text-slate-400">Disponivel agora</div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-5xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16 text-center">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-amber-600 mb-3 block">Como funciona</span>
            <h2 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">Metodologia em 4 passos</h2>
          </motion.div>

          <div className="relative">
            <div className="absolute top-8 left-0 right-0 h-0.5 bg-amber-100 hidden md:block" />
            <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {timeline.map((item, i) => (
                <StaggerItem key={i}>
                  <div className="relative text-center">
                    <motion.div
                      className="w-16 h-16 rounded-full bg-amber-50 border-2 border-amber-200 flex items-center justify-center mx-auto mb-4 relative z-10"
                      whileHover={{ scale: 1.1 }}
                    >
                      <span className="text-lg font-black text-amber-600">{item.step}</span>
                    </motion.div>
                    <h3 className="text-lg font-bold text-slate-900 mb-1">{item.title}</h3>
                    <p className="text-sm text-slate-500">{item.desc}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>
        </div>
      </section>

      {/* Cursos */}
      <section className="py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-amber-600 mb-3 block">Modalidades</span>
            <h2 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">O que ensinamos</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-5">
            {courses.map((c, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                whileHover={{ y: -8 }}
                className="group bg-white rounded-2xl border border-slate-200/60 p-6 hover:shadow-lg hover:border-amber-200 transition-all duration-300"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center group-hover:bg-amber-100 transition-colors">
                    <c.icon size={24} className="text-amber-600" />
                  </div>
                  <ArrowRight size={20} className="text-slate-300 group-hover:text-amber-600 group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{c.title}</h3>
                <p className="text-slate-500 text-sm mb-4">{c.desc}</p>
                <div className="flex gap-4 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <Clock size={12} /> {c.duration}
                  </span>
                  <span className="flex items-center gap-1">
                    <Users size={12} /> {c.students}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-5 bg-slate-900">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              O aprendizado certo muda{" "}
              <span className="text-amber-500">tudo</span>
            </h2>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Falar no WhatsApp"
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
