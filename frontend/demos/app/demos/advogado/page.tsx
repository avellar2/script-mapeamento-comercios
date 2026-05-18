"use client";

import { motion } from "framer-motion";
import { Scale, FileText, Briefcase, Users, BookOpen, ArrowRight, Quote } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#92400e";
const phone = "5511999999003";
const name = "Avellar e Costa";

const areas = [
  { icon: FileText, title: "Direito Civil", desc: "Contratos, responsabilidade civil e regularizacao de imoveis." },
  { icon: Briefcase, title: "Trabalhista", desc: "Reclamacoes, acordos e defesa de empresas." },
  { icon: Users, title: "Familia", desc: "Divorcio, guarda, pensao e partilha de bens." },
  { icon: BookOpen, title: "Empresarial", desc: "Societario, contratos e compliance." },
];

export default function AdvogadoPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#292524" bgColor="#fafaf9" whatsappLabel="Falar com advogado">
      {/* Hero - Editorial, left-aligned, lots of whitespace */}
      <section className="relative min-h-[100dvh] flex items-center bg-[#fafaf9]">
        <div className="absolute top-0 right-0 w-px h-full bg-stone-200 hidden lg:block" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <motion.div
                initial={{ opacity: 0, x: -40 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-px bg-stone-300" />
                  <span className="text-xs font-semibold tracking-[0.2em] uppercase text-stone-500">Escritorio Juridico</span>
                </div>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-stone-900 leading-[0.95] tracking-tight">
                  Direito com{" "}
                  <span className="text-amber-800">discrecao</span>{" "}
                  e excelencia
                </h1>

                <p className="mt-8 text-lg text-stone-500 leading-relaxed max-w-lg font-serif">
                  Atendimento personalizado para voce e sua empresa. Analise criteriosa,
                  comunicacao clara e estrategia juridica alinhada aos seus interesses.
                </p>

                <div className="mt-10 flex flex-col sm:flex-row gap-4 items-start">
                  <MagneticButton
                    phone={phone}
                    label="Falar com advogado"
                    businessName={name}
                    accentColor={accent}
                  />
                </div>

                <div className="mt-16 flex gap-12">
                  {[
                    { value: "15+", label: "Anos de atuacao" },
                    { value: "800+", label: "Casos atendidos" },
                    { value: "100%", label: "Sigilo garantido" },
                  ].map((stat, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 + i * 0.1, duration: 0.6 }}
                    >
                      <div className="text-3xl font-black text-stone-900">{stat.value}</div>
                      <div className="text-xs text-stone-400 mt-1">{stat.label}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>

            <div className="lg:col-span-5">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.3 }}
                className="relative"
              >
                <div className="aspect-[3/4] rounded-lg bg-stone-200 overflow-hidden">
                  <div className="w-full h-full bg-gradient-to-br from-stone-300 to-stone-200 flex items-center justify-center">
                    <Scale size={200} className="text-stone-400 opacity-20" strokeWidth={0.5} />
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Areas - Zig Zag layout */}
      <section className="py-24 px-5">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-px bg-stone-300" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase text-stone-500">Areas de Atuacao</span>
            </div>
            <h2 className="text-3xl md:text-5xl font-black text-stone-900 tracking-tight">Como podemos ajudar</h2>
          </motion.div>

          <div className="space-y-6">
            {areas.map((area, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                className={`group flex flex-col md:flex-row gap-6 items-start p-8 rounded-2xl border border-stone-200/60 hover:border-amber-200 transition-all duration-300 ${i % 2 === 1 ? "md:flex-row-reverse" : ""}`}
              >
                <div className="w-16 h-16 rounded-xl bg-stone-100 flex items-center justify-center flex-shrink-0 group-hover:bg-amber-50 transition-colors">
                  <area.icon size={28} className="text-stone-600 group-hover:text-amber-700 transition-colors" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-stone-900 mb-2">{area.title}</h3>
                  <p className="text-stone-500 leading-relaxed">{area.desc}</p>
                </div>
                <ArrowRight size={20} className="text-stone-300 group-hover:text-amber-700 group-hover:translate-x-1 transition-all flex-shrink-0 mt-1" />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Depoimentos - Editorial */}
      <section className="py-24 px-5 bg-stone-100">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-px bg-stone-300" />
                <span className="text-xs font-semibold tracking-[0.2em] uppercase text-stone-500">Clientes</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-black text-stone-900 tracking-tight">Relacionamentos de confianca</h2>
            </motion.div>

            <StaggerContainer className="space-y-8">
              {[
                { name: "Patricia N.", text: "Dr. Avellar me orientou com clareza em um processo de heranca complicado. Sempre muito atencioso." },
                { name: "Eduardo L.", text: "Atendimento discreto e profissional. Resolveu a situacao trabalhista da minha empresa sem expor ninguem." },
                { name: "Fernanda K.", text: "O escritorio me deu seguranca desde o primeiro contato. Recomendo para qualquer questao juridica." },
              ].map((t, i) => (
                <StaggerItem key={i}>
                  <div className="relative pl-8 border-l-2 border-stone-300">
                    <Quote size={20} className="absolute -left-3 -top-1 text-stone-400 bg-stone-100" />
                    <p className="text-stone-600 leading-relaxed italic">"{t.text}"</p>
                    <p className="text-sm font-bold text-stone-900 mt-4">{t.name}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 px-5">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-12">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-px bg-stone-300" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase text-stone-500">Duvidas</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-black text-stone-900 tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            items={[
              { question: "Qual o valor da consulta?", answer: "A primeira conversa de avaliacao e sem custo. Apos analise do caso, apresentamos um orcamento transparente." },
              { question: "Atendem online?", answer: "Sim. Realizamos consultas por video para clientes de outras cidades." },
              { question: "Como acompanho meu processo?", answer: "Voce recebe atualizacoes periodicas por WhatsApp ou e-mail, com linguagem clara." },
              { question: "O escritorio aceita parcelamento?", answer: "Sim. Oferecemos parcelamento em cartao de credito." },
            ]}
          />
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-32 px-5 bg-stone-900">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Voce nao precisa lidar com isso{" "}
              <span className="text-amber-500">sozinho</span>
            </h2>
            <p className="mt-6 text-lg text-stone-400 max-w-xl mx-auto">
              Fale com um advogado e entenda seus direitos com clareza e seguranca.
            </p>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Falar com advogado"
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
