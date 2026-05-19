"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { MapPin, Clock, Phone, Navigation, Mail } from "lucide-react";
import type { ClientData } from "@/types/client";

export default function LocationSection({ data }: { data: ClientData }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const titles = data.sectionTitles || {};
  const title = titles.location || "Localização";
  const subtitle = titles.locationSubtitle || "Venha nos conhecer";
  const description = (titles as Record<string, string>).locationDescription || "";

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
            <span className="text-sm font-semibold text-primary uppercase tracking-wider">{title}</span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-[1.15]">
              {subtitle}
            </h2>
            {description && (
              <p className="text-base md:text-lg text-muted leading-relaxed">{description}</p>
            )}

            <div className="flex flex-col gap-4 mt-2">
              <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <MapPin size={18} strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Endereço</p>
                  <p className="text-sm text-muted mt-0.5">{data.address}</p>
                </div>
              </div>

              {data.openingHours && (
                <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                    <Clock size={18} strokeWidth={1.5} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">Horário de atendimento</p>
                    <p className="text-sm text-muted mt-0.5 whitespace-pre-line">{data.openingHours}</p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <Phone size={18} strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">Contato</p>
                  {data.phone && <p className="text-sm text-muted mt-0.5">{data.phone}</p>}
                  {data.email && <p className="text-sm text-muted">{data.email}</p>}
                </div>
              </div>

              {data.rating && (
                <div className="flex items-start gap-4 p-4 bg-white rounded-[1rem] border border-border">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                    <Star size={18} strokeWidth={1.5} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">Avaliação</p>
                    <p className="text-sm text-muted mt-0.5">{data.rating} de 5 estrelas · {data.reviewsCount} avaliações</p>
                  </div>
                </div>
              )}
            </div>

            {data.googleMapsUrl && (
              <a
                href={data.googleMapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-slate-700 font-semibold rounded-xl border border-border hover:border-primary/30 hover:text-primary transition-all active:scale-[0.97] mt-2 w-fit"
              >
                <Navigation size={18} />
                Como chegar
              </a>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.1 }}
            className="relative rounded-[1.5rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)] aspect-square lg:aspect-auto lg:h-full min-h-[400px]"
          >
            {data.googleMapsUrl ? (
              <iframe
                src={data.googleMapsUrl}
                className="absolute inset-0 w-full h-full border-0"
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                title={`Localização ${data.businessName}`}
              />
            ) : (
              <div className="absolute inset-0 bg-surface-alt flex items-center justify-center">
                <div className="text-center">
                  <MapPin size={48} className="text-muted mx-auto mb-4" />
                  <p className="text-muted">Mapa indisponível</p>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function Star(props: React.SVGProps<SVGSVGElement> & { size?: number; strokeWidth?: number }) {
  const { size = 18, strokeWidth = 1.5, ...rest } = props;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" {...rest}>
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}