"use client";

import { motion } from "framer-motion";
import { Utensils, Clock, MapPin, Star, Flame, Leaf, ChefHat, Truck, Plus, ShoppingBag } from "lucide-react";
import { DemoLayout } from "@/components/demos/DemoLayout";
import { MagneticButton } from "@/components/demos/MagneticButton";
import { StaggerContainer, StaggerItem } from "@/components/demos/StaggerContainer";
import { FaqSection } from "@/components/demos/FaqSection";

const accent = "#dc2626";
const phone = "5511999999011";
const name = "Sabor Caseiro";

const menuItems = [
  { icon: ChefHat, title: "Marmita Tradicional", desc: "Arroz, feijao, carne e salada. Porcao generosa.", price: "R$ 18", tag: "Mais pedido", color: "#fee2e2" },
  { icon: Flame, title: "Prato do Dia", desc: "Opcoes variadas de segunda a sabado.", price: "R$ 22", tag: "Especial", color: "#fecaca" },
  { icon: Leaf, title: "Marmita Fitness", desc: "Low carb, balanceada e saborosa.", price: "R$ 20", tag: "Saudavel", color: "#fca5a5" },
  { icon: Utensils, title: "Feijoada", desc: "Sabado e domingo. Feijoada completa.", price: "R$ 25", tag: "Weekend", color: "#f87171" },
  { icon: ChefHat, title: "Parmegiana", desc: "Frango ou carne com arroz e fritas.", price: "R$ 28", tag: "Premium", color: "#ef4444" },
  { icon: Truck, title: "Entrega", desc: "Receba seu pedido quentinho em minutos.", price: "R$ 5", tag: "Rapido", color: "#dc2626" },
];

export default function CardapioPage() {
  return (
    <DemoLayout name={name} phone={phone} accentColor={accent} textColor="#450a0a" bgColor="#fef2f2" whatsappLabel="Pedir agora">
      {/* Hero - App-style, food-centric */}
      <section className="relative min-h-[100dvh] flex items-center">
        <div className="absolute inset-0 bg-gradient-to-b from-red-50 to-white" />
        <div className="relative z-10 w-full max-w-7xl mx-auto px-5 py-20 md:py-0">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-red-50 border border-red-200 px-4 py-1.5 text-xs font-semibold text-red-700 mb-8">
                  <Utensils size={12} /> Marmitex e porcoes
                </span>

                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-red-950 leading-[0.95] tracking-tight">
                  Sabor de casa,{" "}
                  <span className="text-red-600">
                    onde voce estiver
                  </span>
                </h1>

                <p className="mt-8 text-lg text-red-900/70 leading-relaxed max-w-lg">
                  Marmitas caseiras, pratos feitos, porcoes e opcoes fresquinhas todos os dias.
                  Peca pelo WhatsApp e receba em minutos.
                </p>

                <div className="mt-10">
                  <MagneticButton
                    phone={phone}
                    label="Pedir agora"
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
                className="relative"
              >
                <div className="aspect-square rounded-[2.5rem] bg-gradient-to-br from-red-100 to-orange-50 flex items-center justify-center">
                  <Utensils size={160} className="text-red-200" strokeWidth={1} />
                </div>
                <motion.div
                  className="absolute -bottom-4 -right-4 bg-white rounded-2xl shadow-xl p-5 border border-red-100"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.6 }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                      <Truck size={20} className="text-green-600" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Entrega rapida</div>
                      <div className="text-xs text-slate-400">30 min na regiao</div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Cardapio - Grid de pratos */}
      <section className="py-24 px-5 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mb-16">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-red-600 mb-3 block">Cardapio</span>
            <h2 className="text-3xl md:text-5xl font-black text-red-950 tracking-tight">O que servimos</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.6 }}
                whileHover={{ y: -8 }}
                className="group bg-white rounded-2xl border border-red-100 overflow-hidden hover:shadow-xl hover:border-red-200 transition-all duration-300"
              >
                <div className="aspect-[16/9] relative" style={{ backgroundColor: item.color }}>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <item.icon size={48} className="text-red-300/50" strokeWidth={1} />
                  </div>
                  <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-bold text-red-900">
                    {item.tag}
                  </div>
                </div>
                <div className="p-5">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-bold text-red-950">{item.title}</h3>
                    <span className="text-lg font-black text-red-600">{item.price}</span>
                  </div>
                  <p className="text-sm text-red-900/60 mb-4">{item.desc}</p>
                  <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-red-50 text-red-700 text-sm font-bold hover:bg-red-100 transition-colors">
                    <Plus size={16} />
                    Adicionar
                  </button>
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
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-red-600 mb-3 block">Clientes</span>
            <h2 className="text-3xl md:text-5xl font-black text-red-950 tracking-tight">Quem prova, repete</h2>
          </motion.div>

          <StaggerContainer className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Roberto S.", text: "Melhor marmita que ja pedi. Parece comida de mae. Sempre peco aqui no almoco." },
              { name: "Ana C.", text: "Opcao fitness salva minha dieta. Saborosa, variada e chega quente." },
              { name: "Diego M.", text: "Entrega rapida e porcao generosa. Custo-beneficio excelente." },
            ].map((t, i) => (
              <StaggerItem key={i}>
                <div className="bg-white rounded-2xl p-6 border border-red-100 shadow-sm h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className="text-red-900/70 text-sm leading-relaxed mb-4">"{t.text}"</p>
                  <p className="text-xs font-bold text-red-950 uppercase tracking-wide">{t.name}</p>
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
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-red-600 mb-3 block">Duvidas</span>
            <h2 className="text-3xl md:text-4xl font-black text-red-950 tracking-tight">Perguntas frequentes</h2>
          </motion.div>
          <FaqSection
            accentColor={accent}
            items={[
              { question: "Qual o horario de funcionamento?", answer: "Funcionamos de segunda a sabado das 10h as 15h. Entregamos ate as 16h." },
              { question: "Tem cardapio do dia?", answer: "Sim. Enviamos o cardapio da semana pelo WhatsApp toda segunda-feira." },
              { question: "Qual o valor da entrega?", answer: "Entregas na regiao custam entre R$ 3 e R$ 7 dependendo da distancia." },
              { question: "Aceita encomenda para eventos?", answer: "Sim. Preparamos marmitas e porcoes para empresas e eventos com valores especiais." },
            ]}
          />
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-32 px-5 bg-red-950">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight leading-[0.95]">
              Comida boa,{" "}
              <span className="text-red-400">
                feita com carinho
              </span>
            </h2>
            <div className="mt-10 flex justify-center">
              <MagneticButton
                phone={phone}
                label="Pedir agora"
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
