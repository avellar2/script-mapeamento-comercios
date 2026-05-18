"use client";

import { motion } from "framer-motion";
import { MapPin, Clock, Phone } from "@phosphor-icons/react";
import { staggerContainer, fadeInUp, slideInRight } from "./motion-variants";

export function Location() {
  return (
    <section className="relative w-full px-6 py-32 md:px-12 lg:px-20">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-center gap-16 md:grid-cols-2">
        {/* Info */}
        <motion.div
          className="flex flex-col items-start gap-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.div className="flex flex-col gap-4" variants={fadeInUp}>
            <p className="text-sm font-medium uppercase tracking-widest text-accent">
              Onde estamos
            </p>
            <h2 className="max-w-[18ch] text-4xl font-semibold leading-[0.95] tracking-tighter text-text-primary md:text-5xl">
              Visite nosso ateliê.
            </h2>
          </motion.div>

          <motion.div
            className="flex flex-col gap-6"
            variants={staggerContainer}
          >
            <motion.div
              className="flex items-start gap-4"
              variants={fadeInUp}
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                <MapPin size={22} weight="duotone" />
              </div>
              <div>
                <p className="font-semibold text-text-primary">Endereço</p>
                <p className="mt-0.5 text-text-secondary">
                  Rua Oscar Freire, 847 — Jardins
                  <br />
                  São Paulo, SP
                </p>
              </div>
            </motion.div>

            <motion.div
              className="flex items-start gap-4"
              variants={fadeInUp}
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                <Clock size={22} weight="duotone" />
              </div>
              <div>
                <p className="font-semibold text-text-primary">Horário de Atendimento</p>
                <p className="mt-0.5 text-text-secondary">
                  Terça a Sexta: 09h às 19h
                  <br />
                  Sábado: 09h às 14h
                </p>
              </div>
            </motion.div>

            <motion.div
              className="flex items-start gap-4"
              variants={fadeInUp}
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                <Phone size={22} weight="duotone" />
              </div>
              <div>
                <p className="font-semibold text-text-primary">Contato</p>
                <p className="mt-0.5 text-text-secondary">
                  +55 (11) 99876-5432
                  <br />
                  contato@bellaface.com.br
                </p>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Map */}
        <motion.div
          className="relative aspect-[4/3] w-full overflow-hidden rounded-[2rem] md:aspect-square"
          variants={slideInRight}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
        >
          <iframe
            src="https://www.openstreetmap.org/export/embed.html?bbox=-46.6756%2C-23.5665%2C-46.6656%2C-23.5565&layer=mapnik&marker=-23.5615%2C-46.6706"
            className="absolute inset-0 h-full w-full border-0 grayscale-[20%]"
            loading="lazy"
            title="Localização Studio Bella Face"
          />
          <div className="absolute inset-0 rounded-[2rem] shadow-[inset_0_0_0_1px_rgba(0,0,0,0.06)]" />
        </motion.div>
      </div>
    </section>
  );
}
