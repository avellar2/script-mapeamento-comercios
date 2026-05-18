"use client";

import { motion } from "framer-motion";
import { Home, Key, MapPin, TrendingUp, Search, Star, ChevronRight, Bath, Bed, Ruler } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#059669";
const phone = "5511999999005";
const name = "Morar Bem";

const properties = [
  { title: "Apartamento Moderno", location: "Centro", price: "R$ 450.000", beds: 2, baths: 1, area: "65m²", color: "#d1fae5" },
  { title: "Casa Familiar", location: "Bairro Nobre", price: "R$ 780.000", beds: 3, baths: 2, area: "120m²", color: "#a7f3d0" },
  { title: "Studio Premium", location: "Metro", price: "R$ 320.000", beds: 1, baths: 1, area: "45m²", color: "#6ee7b7" },
  { title: "Cobertura Vista", location: "Vista Panoramica", price: "R$ 1.200.000", beds: 4, baths: 3, area: "200m²", color: "#34d399" },
  { title: "Salao Comercial", location: "Avenida Principal", price: "R$ 650.000", beds: 0, baths: 2, area: "150m²", color: "#10b981" },
];

export default function ImobiliariaPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#1c1917" bgColor="#fafaf9" whatsappLabel="Falar com corretor">
      {/* Hero - Masonry-style aspiracional */}
      <section className="relative min-h-[100dvh] flex items-center">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-50/50 to-transparent" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 border border-emerald-200 px-4 py-1.5 text-xs font-semibold text-emerald-700 mb-8">
                  <Key size={12} /> Imoveis selecionados
                </span>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-stone-900 leading-[0.95] tracking-tight">
                  A chave do seu{" "}
                  <span className="text-emerald-700">
                    novo lar
                  </span>
                </h1>

                <p className="mt-8 text-lg text-stone-500 leading-relaxed max-w-lg">
                  Apartamentos, casas e lancamentos com curadoria de quem entende do mercado.
                  Atendimento direto e sem burocracia.
                </p>

                <div className="mt-10">
                  <MagneticButton
                    phone={phone}
                    label="Falar com corretor"
                    businessName={name}
                    accentColor={accent}
                  />
                </div>
              </motion.div>
            </div>

            <div className="hidden lg:block">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 1, delay: 0.2 }}
                className="grid grid-cols-2 gap-3"
              >
                <div className="space-y-3">
                  <div className="aspect-[3/4] rounded-2xl bg-emerald-100" />
                  <div className="aspect-square rounded-2xl bg-emerald-200" />
                </div>
                <div className="space-y-3 pt-8">
                  <div className="aspect-square rounded-2xl bg-emerald-50" />
                  <div className="aspect-[3/4] rounded-2xl bg-emerald-100" />
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Imoveis - Masonry */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-emerald-600 mb-3 block">Galeria</span>
            <h2 className="text-3xl md:text-5xl font-black text-stone-900 tracking-tight">Imoveis disponiveis</h2>
          </motion.div>

          <StaggerContainer className="columns-1 md:columns-2 lg:columns-3 gap-5">
            {properties.map((prop, i) => (
              <StaggerItem key={i} className="break-inside-avoid mb-5">
                <motion.div
                  className="group rounded-2xl overflow-hidden border border-stone-200/60 bg-white hover:shadow-xl transition-all duration-300"
                  whileHover={{ y: -4 }}
                >
                  <div className="aspect-[4/3] relative" style={{ backgroundColor: prop.color }}>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Home size={48} className="text-emerald-700/20" strokeWidth={1} />
                    </div>
                    <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-bold text-stone-900">
                      {prop.price}
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="text-lg font-bold text-stone-900 mb-1">{prop.title}</h3>
                    <div className="flex items-center gap-1 text-sm text-stone-500 mb-3">
                      <MapPin size={14} />
                      {prop.location}
                    </div>
                    <div className="flex gap-4 text-xs text-stone-500">
                      <span className="flex items-center gap-1">
                        <Bed size={14} /> {prop.beds}
                      </span>
                      <span className="flex items-center gap-1">
                        <Bath size={14} /> {prop.baths}
                      </span>
                      <span className="flex items-center gap-1">
                        <Ruler size={14} /> {prop.area}
                      </span>
                    </div>
                  </div>
                </motion.div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* Depoimentos */}
      <section className="py-24 px-5 bg-stone-100">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-emerald-600 mb-3 block">Clientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-stone-900 tracking-tight">Quem comprou, recomenda</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Rafael T.", text: "O corretor me mostrou opcoes que realmente faziam sentido para o meu perfil." },
              { name: "Debora M.", text: "Vendi meu apartamento em 3 semanas com o preco que eu queria. Atendimento impecavel." },
              { name: "Carlos E.", text: "Negociacao transparente do inicio ao fim. Nenhuma surpresa desagradavel." },
            ].map((t, i) => (
              <StaggerItem key={i}>
                <div className="bg-white rounded-2xl p-6 border border-stone-200/50 h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className="text-stone-600 text-sm leading-relaxed mb-4">"{t.text}"</p>
                  <p className="text-xs font-bold text-stone-900 uppercase tracking-wide">{t.name}</p>
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
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-emerald-600 mb-3 block">Duvidas</span>
            <h2 className="text-3xl md:text-4xl font-black text-stone-900 tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            items={[
              { question: "Preciso pagar algum valor para iniciar?", answer: "Nao. O atendimento inicial e a visita ao imovel sao totalmente gratuitos." },
              { question: "Voces fazem aprovacao de financiamento?", answer: "Sim. Acompanhamos voce em todo o processo de aprovacao com os bancos parceiros." },
              { question: "Como agendo uma visita?", answer: "E so mandar uma mensagem pelo WhatsApp com o codigo do imovel ou descrever o que procura." },
              { question: "Tem imovel para locacao?", answer: "Sim. Trabalhamos com carteira propria de locacao e tambem imoveis de terceiros." },
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
              O seu imovel esta mais perto do que voce{" "}
              <span className="text-emerald-500">imagina</span>
            </h2>
            <p className="mt-6 text-lg text-stone-400 max-w-xl mx-auto">
              Fale com um corretor experiente e encontre o imovel ideal para voce.
            </p>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Falar com corretor"
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
