"use client";

import { motion } from "framer-motion";
import { Shield, Smile, Heart, Sparkles, Star, Clock, MapPin, Check } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#0ea5e9";
const phone = "5511999999002";
const name = "Sorriso Prime";

const treatments = [
  { icon: Smile, title: "Clareamento", desc: "Tecnologia segura para um sorriso mais branco." },
  { icon: Heart, title: "Tratamento de Canal", desc: "Procedimento moderno e com anestesia eficaz." },
  { icon: Sparkles, title: "Proteses", desc: "Materiais de alta durabilidade." },
  { icon: Shield, title: "Prevencao", desc: "Remocao de tartaro e controle de caries." },
];

const bentoItems = [
  { title: "20+", subtitle: "Anos de experiencia", span: "col-span-2" },
  { title: "5.000+", subtitle: "Pacientes atendidos" },
  { title: "4.9", subtitle: "Avaliacao media", stars: true },
  { title: "Seg", subtitle: "a Sabado" },
];

export default function DentistaPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#0f172a" bgColor="#ffffff" whatsappLabel="Agendar avaliação">
      {/* Hero - Clean, left-aligned, whitespace generoso */}
      <section className="relative min-h-[100dvh] flex items-center bg-white">
        <div className="absolute top-0 right-0 w-[60%] h-full bg-gradient-to-l from-sky-50 to-transparent opacity-50" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid md:grid-cols-5 gap-12 items-center">
            <div className="md:col-span-3">
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-sky-50 border border-sky-100 px-4 py-1.5 text-xs font-semibold text-sky-600 mb-8">
                  <Shield size={12} /> Protocolo de higiene reforcado
                </span>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-slate-900 leading-[0.95] tracking-tight">
                  Cuidado que{" "}
                  <span className="text-sky-500">transforma</span>{" "}
                  sorrisos
                </h1>

                <p className="mt-8 text-lg text-slate-500 leading-relaxed max-w-lg">
                  Agende sua avaliacao com conforto, tecnologia e um time que se importa de verdade com a sua saude bucal.
                </p>

                <div className="mt-10 flex flex-col sm:flex-row gap-4 items-start">
                  <MagneticButton
                    phone={phone}
                    label="Agendar avaliação"
                    businessName={name}
                    accentColor={accent}
                  />
                </div>

                <div className="mt-12 flex items-center gap-6">
                  <div className="flex -space-x-3">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="w-10 h-10 rounded-full border-2 border-white bg-sky-100 flex items-center justify-center text-xs font-bold text-sky-600"
                      >
                        {String.fromCharCode(64 + i)}
                      </div>
                    ))}
                  </div>
                  <div>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={14} className="text-amber-400 fill-amber-400" />
                      ))}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">4.9 de 2.400 avaliacoes</p>
                  </div>
                </div>
              </motion.div>
            </div>

            <div className="md:col-span-2">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 1, delay: 0.2, ease: [0.23, 1, 0.32, 1] }}
                className="relative"
              >
                <div className="aspect-[4/5] rounded-[2rem] bg-gradient-to-br from-sky-100 to-sky-50 flex items-center justify-center overflow-hidden">
                  <Smile size={120} className="text-sky-200" strokeWidth={1} />
                </div>
                <motion.div
                  className="absolute -bottom-6 -left-6 bg-white rounded-2xl shadow-xl p-4 border border-slate-100"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.6 }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      <Clock size={18} className="text-green-600" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Horarios flexiveis</div>
                      <div className="text-xs text-slate-400">Agende pelo WhatsApp</div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Bento Grid Stats */}
      <section className="py-24 px-5 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {bentoItems.map((item, i) => (
              <StaggerItem key={i} className={item.span || ""}>
                <motion.div
                  className="bg-white rounded-[2rem] p-8 border border-slate-200/50 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)] h-full flex flex-col justify-center"
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                >
                  <div className="text-4xl md:text-5xl font-black text-slate-900">{item.title}</div>
                  <div className="text-sm text-slate-500 mt-2">{item.subtitle}</div>
                  {item.stars && (
                    <div className="flex gap-1 mt-3">
                      {Array.from({ length: 5 }).map((_, j) => (
                        <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                      ))}
                    </div>
                  )}
                </motion.div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* Tratamentos - Horizontal scroll */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-sky-500 mb-3 block">Tratamentos</span>
            <h2 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">Cuidamos de todo o seu sorriso</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {treatments.map((t, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
                whileHover={{ y: -8, transition: { duration: 0.2 } }}
                className="group bg-white rounded-2xl border border-slate-200/60 p-6 hover:shadow-lg hover:border-sky-200 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-sky-50 flex items-center justify-center mb-4 group-hover:bg-sky-100 transition-colors">
                  <t.icon size={22} className="text-sky-500" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{t.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{t.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Depoimentos */}
      <section className="py-24 px-5 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-sky-500 mb-3 block">Pacientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">Quem cuida, recomenda</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Camila S.", text: "Atendimento delicado e ambiente limpo. Me senti segura do inicio ao fim.", rating: 5 },
              { name: "Ricardo M.", text: "Consegui agendar pelo WhatsApp de madrugada e atenderam no mesmo dia.", rating: 5 },
              { name: "Ana P. T.", text: "Dr. explicou cada passo do tratamento. Nunca me senti tao tranquila no dentista.", rating: 5 },
            ].map((t, i) => (
              <StaggerItem key={i}>
                <div className="bg-white rounded-2xl p-6 border border-slate-200/50 h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: t.rating }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className="text-slate-600 text-sm leading-relaxed mb-4">"{t.text}"</p>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">{t.name}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-12">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-sky-500 mb-3 block">Duvidas</span>
            <h2 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            items={[
              { question: "Preciso de encaminhamento?", answer: "Nao. Basta agendar sua avaliacao pelo WhatsApp. Atendemos particulares e convenios." },
              { question: "O tratamento dói?", answer: "Utilizamos anestesia moderna e tecnicas minimamente invasivas para o seu conforto." },
              { question: "Posso parcelar?", answer: "Sim. Aceitamos cartao de credito em ate 10x e PIX a vista com desconto." },
              { question: "Qual o horario de funcionamento?", answer: "Segunda a sexta das 8h as 19h e sabado das 8h as 13h. Atendimento com hora marcada." },
            ]}
          />
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-32 px-5 bg-slate-50">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-slate-900 tracking-tight leading-[0.95]">
              Seu sorriso merece{" "}
              <span className="text-sky-500">atencao de verdade</span>
            </h2>
            <p className="mt-6 text-lg text-slate-500 max-w-xl mx-auto">
              Agende agora sua avaliacao e comece a cuidar da sua saude bucal com quem entende.
            </p>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Agendar avaliacao"
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
