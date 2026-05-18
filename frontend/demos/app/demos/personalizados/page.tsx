"use client";

import { motion } from "framer-motion";
import { Gift, Cake, Palette, Heart, Star, Sparkles, ArrowRight, Package } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#ec4899";
const phone = "5511999999008";
const name = "Doce Encanto";

const products = [
  { icon: Gift, title: "Lembrancinhas", desc: "Canecas, azulejos, chinelos e brindes personalizados.", price: "A partir de R$ 15", color: "#fce7f3" },
  { icon: Cake, title: "Doces e Bolos", desc: "Brigadeiros gourmet, cupcakes e bolos decorados.", price: "A partir de R$ 50", color: "#fbcfe8" },
  { icon: Palette, title: "Decoracao", desc: "Toppers, paineis, baloes e kits festa.", price: "A partir de R$ 30", color: "#f9a8d4" },
  { icon: Package, title: "Kits Especiais", desc: "Cestas de cafe da manha e presentes.", price: "A partir de R$ 80", color: "#f472b6" },
];

export default function PersonalizadosPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#831843" bgColor="#fdf2f8" whatsappLabel="Pedir orcamento">
      {/* Hero - Delicate, warm, playful */}
      <section className="relative min-h-[100dvh] flex items-center">
        <div className="absolute top-0 right-0 w-[60%] h-full bg-gradient-to-l from-pink-50 to-transparent" />
        <div className="absolute top-20 left-20 w-32 h-32 bg-pink-200/30 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-48 h-48 bg-rose-200/20 rounded-full blur-3xl" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-pink-50 border border-pink-200 px-4 py-1.5 text-xs font-semibold text-pink-700 mb-8">
                  <Heart size={12} /> Feito com carinho
                </span>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-pink-950 leading-[0.95] tracking-tight">
                  Detalhes que fazem a{" "}
                  <span className="text-pink-600">
                    festa brilhar
                  </span>
                </h1>

                <p className="mt-8 text-lg text-pink-900/70 leading-relaxed max-w-lg">
                  Canecas, azulejos, lembrancinhas, toppers, doces, bolos e decoracao.
                  Tudo personalizado para tornar seu momento unico.
                </p>

                <div className="mt-10">
                  <MagneticButton
                    phone={phone}
                    label="Pedir orcamento"
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
                className="grid grid-cols-2 gap-4"
              >
                <motion.div
                  className="aspect-[3/4] rounded-3xl bg-gradient-to-br from-pink-100 to-rose-100 flex items-center justify-center"
                  animate={{ y: [0, -10, 0] }}
                  transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                >
                  <Gift size={80} className="text-pink-300" strokeWidth={1} />
                </motion.div>
                <motion.div
                  className="aspect-[3/4] rounded-3xl bg-gradient-to-br from-rose-100 to-pink-100 flex items-center justify-center mt-8"
                  animate={{ y: [0, 10, 0] }}
                  transition={{ repeat: Infinity, duration: 4, ease: "easeInOut", delay: 1 }}
                >
                  <Cake size={80} className="text-rose-300" strokeWidth={1} />
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Produtos - Grid colorido */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-pink-600 mb-3 block">Produtos</span>
            <h2 className="text-3xl md:text-5xl font-black text-pink-950 tracking-tight">O que criamos para voce</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {products.map((p, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                whileHover={{ y: -8 }}
                className="group relative rounded-3xl overflow-hidden"
              >
                <div className="aspect-[16/10] relative" style={{ backgroundColor: p.color }}>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <p.icon size={64} className="text-pink-400/30" strokeWidth={1} />
                  </div>
                  <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-bold text-pink-900">
                    {p.price}
                  </div>
                </div>
                <div className="p-6 bg-white border-x border-b border-pink-100 rounded-b-3xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-pink-950 mb-1">{p.title}</h3>
                      <p className="text-sm text-pink-900/60">{p.desc}</p>
                    </div>
                    <ArrowRight size={20} className="text-pink-300 group-hover:text-pink-600 group-hover:translate-x-1 transition-all flex-shrink-0" />
                  </div>
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
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-pink-600 mb-3 block">Clientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-pink-950 tracking-tight">Quem encomenda, elogia</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Tatiane R.", text: "As lembrancinhas ficaram lindas! Todos os convidados perguntaram onde encomendei." },
              { name: "Carlos M.", text: "Bolo de aniversario do meu filho superou a expectativa. Detalhes impecaveis." },
              { name: "Priscila L.", text: "Entrega pontual e embalagem perfeita. Voces capricham em tudo." },
            ].map((t, i) => (
              <StaggerItem key={i}>
                <div className="bg-white rounded-2xl p-6 border border-pink-100 shadow-sm h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className="text-pink-900/70 text-sm leading-relaxed mb-4">"{t.text}"</p>
                  <p className="text-xs font-bold text-pink-900 uppercase tracking-wide">{t.name}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-5 bg-pink-950">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Sua festa merece{" "}
              <span className="text-pink-400">
                carinho em cada detalhe
              </span>
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
