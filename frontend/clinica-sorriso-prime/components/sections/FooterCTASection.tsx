"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Phone, ArrowRight, MessageCircle } from "lucide-react";
import type { ClientData } from "@/types/client";
import { createWhatsAppLink } from "@/lib/whatsapp";

export default function FooterCTASection({ data }: { data: ClientData }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const waLink = createWhatsAppLink(data.whatsapp, data.businessName);
  const titles = data.sectionTitles || {};
  const title = titles.cta || `Pronto para começar?`;
  const subtitle = titles.ctaSubtitle || data.ctaText || "Entre em contato pelo WhatsApp. Nossa equipe responde em minutos.";
  const ctaLabel = data.ctaLabel || "Fale conosco";

  return (
    <section className="py-20 md:py-32 bg-primary relative overflow-hidden" ref={ref}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -left-40 w-[400px] h-[400px] rounded-full bg-white/5 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full bg-white/5 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] rounded-full border border-white/10" />
      </div>

      <div className="relative max-w-[800px] mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="flex flex-col items-center gap-6 md:gap-8"
        >
          <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center">
            <MessageCircle size={28} className="text-white" />
          </div>

          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-[1.15]">
            {title}
          </h2>

          <p className="text-base md:text-lg text-white/80 leading-relaxed max-w-lg">
            {subtitle}
          </p>

          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2">
            <a
              href={waLink}
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-white text-primary font-semibold rounded-xl hover:bg-white/95 transition-all active:scale-[0.97] shadow-lg"
            >
              <Phone size={18} strokeWidth={2} />
              {ctaLabel} pelo WhatsApp
              <ArrowRight size={16} strokeWidth={2} className="group-hover:translate-x-0.5 transition-transform" />
            </a>
          </div>

          <p className="text-sm text-white/60">
            Atendimento rápido · Resposta em minutos
          </p>
        </motion.div>
      </div>
    </section>
  );
}