"use client";

import { motion } from "framer-motion";
import { MapPin, Clock, Phone } from "@phosphor-icons/react";

export function Location() {
  return (
    <section className="relative w-full">
      <div className="relative h-[480px] w-full md:h-[580px]">
        <iframe
          src="https://www.openstreetmap.org/export/embed.html?bbox=-46.6580%2C-23.5600%2C-46.6480%2C-23.5500&layer=mapnik&marker=-23.5550%2C-46.6530"
          className="absolute inset-0 h-full w-full border-0"
          loading="lazy"
          title="Localização Abrasileirado"
        />

        {/* Boteco facade overlay panel */}
        <motion.div
          className="absolute bottom-6 left-6 right-6 z-20 overflow-hidden rounded-lg border-4 border-wood bg-cream shadow-2xl md:bottom-auto md:left-12 md:right-auto md:top-1/2 md:w-[420px] md:-translate-y-1/2"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          {/* Awning top */}
          <div className="flex">
            {Array.from({ length: 12 }).map((_, i) => (
              <div
                key={i}
                className={`h-8 flex-1 ${i % 2 === 0 ? "bg-red" : "bg-cream"}`}
                style={{
                  clipPath: "polygon(0 0, 100% 0, 85% 100%, 15% 100%)",
                }}
              />
            ))}
          </div>

          <div className="p-6 md:p-8">
            <p className="mb-6 text-sm font-bold uppercase tracking-widest text-accent">
              Onde estamos
            </p>

            <div className="flex flex-col gap-5">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                  <MapPin size={20} weight="duotone" />
                </div>
                <div>
                  <p className="font-bold text-wood">Endereço</p>
                  <p className="text-sm text-text-secondary">
                    Rua dos Sabores, 456 — Centro
                    <br />São Paulo, SP
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                  <Clock size={20} weight="duotone" />
                </div>
                <div>
                  <p className="font-bold text-wood">Horário</p>
                  <p className="text-sm text-text-secondary">
                    Segunda a Sexta: 11h às 15h
                    <br />Sábado: 11h às 14h
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                  <Phone size={20} weight="duotone" />
                </div>
                <div>
                  <p className="font-bold text-wood">Contato</p>
                  <p className="text-sm text-text-secondary">
                    +55 (11) 98765-4321
                    <br />pedidos@abrasileirado.com.br
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Wood bottom trim */}
          <div className="h-3 bg-wood" />
        </motion.div>
      </div>
    </section>
  );
}
