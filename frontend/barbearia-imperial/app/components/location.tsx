"use client";

import { motion } from "framer-motion";
import { MapPin, Clock, Phone } from "@phosphor-icons/react";

export function Location() {
  return (
    <section className="relative w-full">
      {/* Full bleed map */}
      <div className="relative h-[600px] w-full md:h-[700px]">
        <iframe
          src="https://www.openstreetmap.org/export/embed.html?bbox=-46.6580%2C-23.5600%2C-46.6480%2C-23.5500&layer=mapnik&marker=-23.5550%2C-46.6530"
          className="absolute inset-0 h-full w-full border-0 grayscale-[30%]"
          loading="lazy"
          title="Localização Barbearia Imperial"
        />

        {/* Glassmorphism panel */}
        <motion.div
          className="absolute bottom-8 left-6 right-6 z-20 rounded-[1.5rem] border border-white/10 bg-background/80 p-6 shadow-2xl backdrop-blur-xl md:bottom-auto md:left-12 md:right-auto md:top-1/2 md:w-[420px] md:-translate-y-1/2 md:p-8"
          style={{
            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.1), 0 20px 40px -15px rgba(0,0,0,0.5)",
          }}
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <p className="mb-6 text-sm font-medium uppercase tracking-widest text-accent">Onde estamos</p>

          <div className="flex flex-col gap-5">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <MapPin size={20} weight="duotone" />
              </div>
              <div>
                <p className="font-semibold text-text-primary">Endereço</p>
                <p className="text-sm text-text-secondary">
                  Rua Augusta, 1271 — Consolação
                  <br />São Paulo, SP
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <Clock size={20} weight="duotone" />
              </div>
              <div>
                <p className="font-semibold text-text-primary">Horário</p>
                <p className="text-sm text-text-secondary">
                  Terça a Sáb: 10h às 21h
                  <br />Domingo: 10h às 16h
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <Phone size={20} weight="duotone" />
              </div>
              <div>
                <p className="font-semibold text-text-primary">Contato</p>
                <p className="text-sm text-text-secondary">
                  +55 (11) 98765-4321
                  <br />contato@barbeariaimperial.com.br
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
