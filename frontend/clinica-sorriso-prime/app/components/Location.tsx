"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { MapPin, Clock, Phone, Navigation } from "lucide-react";

export default function Location() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="localizacao" className="py-20 md:py-32 bg-surface" ref={ref}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="flex flex-col gap-6"
          >
            <span className="text-sm font-semibold text-primary uppercase tracking-wider">Localização</span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-[1.15]">
              Venha nos conhecer
            </h2>
            <p className="text-base md:text-lg text-muted leading-relaxed">
              Estamos em uma região de fácil acesso, com estacionamento próximo e transporte público à porta.
            </p>

            <div className="flex flex-col gap-4 mt-2">
              <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <MapPin size={18} strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Endereço</p>
                  <p className="text-sm text-muted mt-0.5">
                    Rua Oscar Freire, 1234 - Jardins
                    <br />
                    São Paulo - SP, 05409-012
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <Clock size={18} strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Horário de atendimento</p>
                  <p className="text-sm text-muted mt-0.5">
                    Segunda a Sexta: 8h às 20h
                    <br />
                    Sábado: 8h às 14h
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <Phone size={18} strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Contato</p>
                  <p className="text-sm text-muted mt-0.5">(11) 99999-9999</p>
                  <p className="text-sm text-muted">contato@sorrisoprime.com.br</p>
                </div>
              </div>
            </div>

            <a
              href="https://maps.google.com/?q=Rua+Oscar+Freire+1234+Sao+Paulo"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-slate-700 font-semibold rounded-xl border border-border hover:border-primary/30 hover:text-primary transition-all active:scale-[0.97] mt-2 w-fit"
            >
              <Navigation size={18} />
              Como chegar
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.1 }}
            className="relative rounded-[1.5rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)] aspect-square lg:aspect-auto lg:h-full min-h-[400px]"
          >
            <iframe
              src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3657.197587765244!2d-46.674272!3d-23.561763!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94ce578f0ea6f5f7%3A0x8a5e1c6e7d3c3e0e!2sRua%20Oscar%20Freire!5e0!3m2!1spt-BR!2sbr!4v1234567890"
              className="absolute inset-0 w-full h-full border-0"
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              title="Localização da Clínica Sorriso Prime"
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
