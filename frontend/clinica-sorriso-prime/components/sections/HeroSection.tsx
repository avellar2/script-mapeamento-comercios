"use client";

import { motion } from "framer-motion";
import { ArrowRight, Phone, Calendar } from "lucide-react";
import type { ClientData } from "@/types/client";
import { createWhatsAppLink } from "@/lib/whatsapp";

export default function HeroSection({ data }: { data: ClientData }) {
  const waLink = createWhatsAppLink(data.whatsapp, data.businessName);
  const ctaLabel = data.ctaLabel || "Agendar";
  const trustSignals = data.trustSignals || [];
  const heroImages = data.images.hero || [];

  return (
    <section className="relative min-h-[100dvh] flex items-center overflow-hidden bg-surface">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-[400px] h-[400px] rounded-full bg-accent/5 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[300px] h-[300px] rounded-full bg-primary-light/10 blur-3xl" />
      </div>

      <div className="relative max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32 w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ type: "spring", stiffness: 80, damping: 20 }}
            className="flex flex-col gap-6 md:gap-8"
          >
            {data.rating && (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white rounded-full border border-border shadow-[0_1px_2px_rgba(0,0,0,0.04)] w-fit">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
                  {data.rating} ★ · {data.reviewsCount} avaliações
                </span>
              </div>
            )}

            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-[4rem] font-bold tracking-tighter leading-[1.1] text-slate-900">
              {data.headline.split(" ").map((word, i, arr) =>
                i === Math.floor(arr.length / 2) ? (
                  <span key={i} className="text-primary">
                    {word}{" "}
                  </span>
                ) : (
                  <span key={i}>{word} </span>
                )
              )}
            </h1>

            <p className="text-base md:text-lg text-muted leading-relaxed max-w-[50ch]">
              {data.subheadline}
            </p>

            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2">
              <a
                href={waLink}
                target="_blank"
                rel="noopener noreferrer"
                className="group inline-flex items-center justify-center gap-2.5 px-6 py-3.5 bg-primary text-white font-semibold rounded-xl hover:bg-primary-dark transition-all active:scale-[0.97] shadow-[0_1px_3px_rgba(0,0,0,0.1)]"
              >
                <Phone size={18} strokeWidth={2} />
                {ctaLabel}
                <ArrowRight size={16} strokeWidth={2} className="group-hover:translate-x-0.5 transition-transform" />
              </a>

              <a
                href="#servicos"
                className="group inline-flex items-center justify-center gap-2.5 px-6 py-3.5 bg-white text-slate-700 font-semibold rounded-xl border border-border hover:border-primary/30 hover:text-primary transition-all active:scale-[0.97]"
              >
                <Calendar size={18} strokeWidth={2} />
                Conhecer serviços
              </a>
            </div>

            {trustSignals.length > 0 && (
              <div className="flex items-center gap-6 pt-4 text-sm text-muted">
                {trustSignals.slice(0, 2).map((signal) => (
                  <div key={signal} className="flex items-center gap-2">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-success">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    <span>{signal}</span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {heroImages.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ type: "spring", stiffness: 80, damping: 20, delay: 0.1 }}
              className="relative hidden lg:grid grid-cols-12 gap-4 h-[520px]"
            >
              <div className="col-span-7 row-span-2 relative rounded-[2rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
                <img
                  src={heroImages[0]}
                  alt={data.businessName}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/20 to-transparent" />
              </div>
              {heroImages[1] && (
                <div className="col-span-5 row-span-1 relative rounded-[2rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
                  <img
                    src={heroImages[1]}
                    alt={data.businessName}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              {heroImages[2] ? (
                <div className="col-span-5 row-span-1 relative rounded-[2rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
                  <img
                    src={heroImages[2]}
                    alt={data.businessName}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="col-span-5 row-span-1 relative rounded-[2rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)] bg-primary/5 flex items-center justify-center p-6">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-primary">★ {data.rating || "5.0"}</p>
                    <p className="text-sm text-slate-600 mt-1">{data.reviewsCount || "0"} avaliações</p>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}