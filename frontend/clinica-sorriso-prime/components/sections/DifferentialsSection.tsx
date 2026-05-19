"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import {
  Heart, Home, GraduationCap, Monitor, CalendarCheck,
  Shield, FileText, UserCheck, MessageCircle, Award,
  Clock, ThumbsUp, Star, CheckCircle, Leaf
} from "lucide-react";
import type { ClientData, DifferentialItem } from "@/types/client";

const iconMap: Record<string, React.ComponentType<{ size?: number; strokeWidth?: number }>> = {
  Heart, Home, GraduationCap, Monitor, CalendarCheck, Shield, FileText,
  UserCheck, MessageCircle, Award, Clock, ThumbsUp, Star, CheckCircle, Leaf,
};

function getIcon(iconName?: string) {
  if (!iconName) return CheckCircle;
  return iconMap[iconName] || CheckCircle;
}

export default function DifferentialsSection({ data }: { data: ClientData }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const titles = data.sectionTitles || {};
  const title = titles.differentials || "Diferenciais";
  const subtitle = titles.differentialsSubtitle || `Por que escolher a ${data.businessName}?`;
  const description = (titles as Record<string, string>).differentialsDescription || "";
  const items = data.differentialItems || data.differentials.map((d) => ({
    title: d,
    description: "",
    icon: "CheckCircle",
  }));
  const heroImages = data.images.hero || [];

  if (items.length === 0) return null;

  return (
    <section id="diferenciais" className="py-20 md:py-32 bg-surface" ref={ref}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="lg:sticky lg:top-28"
          >
            <span className="text-sm font-semibold text-primary uppercase tracking-wider">{title}</span>
            <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-[1.15]">
              {subtitle.includes("Sorriso Prime") ? subtitle : subtitle}
            </h2>
            {description && (
              <p className="mt-5 text-base md:text-lg text-muted leading-relaxed max-w-md">{description}</p>
            )}

            {heroImages[0] && (
              <div className="hidden lg:block mt-10 relative rounded-[2rem] overflow-hidden aspect-[4/3] shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
                <img
                  src={heroImages[0]}
                  alt={data.businessName}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/30 to-transparent" />
                <div className="absolute bottom-6 left-6 right-6">
                  <p className="text-white font-semibold text-lg">Seu bem-estar em primeiro lugar</p>
                </div>
              </div>
            )}
          </motion.div>

          <div className="flex flex-col gap-4">
            {items.map((item: DifferentialItem, i: number) => {
              const Icon = getIcon(item.icon);
              return (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, y: 30 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ type: "spring", stiffness: 100, damping: 20, delay: i * 0.1 }}
                  className="group flex gap-5 p-6 md:p-7 bg-white rounded-[1.5rem] border border-border hover:border-primary/20 hover:shadow-[0_12px_30px_-10px_rgba(0,0,0,0.06)] transition-all duration-300"
                >
                  <div className="shrink-0 w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary group-hover:text-white text-primary transition-colors">
                    <Icon size={22} strokeWidth={1.5} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-1.5">{item.title}</h3>
                    <p className="text-sm text-muted leading-relaxed">{item.description}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}