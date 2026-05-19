"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import {
  Sparkles, Shield, Smile, Target, ArrowRight, Heart, Home,
  GraduationCap, Monitor, CalendarCheck, Briefcase, Scale,
  Users, FileText, UserCheck, MessageCircle, Code, Wrench,
  Truck, Car, Building, BookOpen, Scissors, Utensils, Stethoscope,
  Church, GraduationCap as CourseIcon, Store
} from "lucide-react";
import type { ClientData, ServiceItem } from "@/types/client";

const iconMap: Record<string, React.ComponentType<{ size?: number; strokeWidth?: number }>> = {
  Target, Sparkles, Smile, AlignCenter: Users, Bone: Shield, Wrench, Shield,
  Heart, Home, GraduationCap, Monitor, CalendarCheck, Briefcase, Scale,
  Users, FileText, UserCheck, MessageCircle, Code, Truck, Car, Building,
  BookOpen, Scissors, Utensils, Stethoscope, Church, CourseIcon, Store,
};

function getIcon(iconName?: string) {
  if (!iconName) return Sparkles;
  return iconMap[iconName] || Sparkles;
}

function ServiceCard({ item, index, colorClass }: { item: ServiceItem; index: number; colorClass: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  const Icon = getIcon(item.icon);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ type: "spring", stiffness: 100, damping: 20, delay: index * 0.08 }}
      className="group relative flex flex-col gap-4 p-6 md:p-8 bg-white rounded-[1.5rem] border border-border hover:border-primary/20 hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.06)] transition-all duration-300"
    >
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClass}`}>
        <Icon size={22} strokeWidth={1.5} />
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.title}</h3>
        <p className="text-sm text-muted leading-relaxed">{item.description}</p>
      </div>
      <div className="flex items-center gap-1 text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
        <span>Saiba mais</span>
        <ArrowRight size={14} />
      </div>
    </motion.div>
  );
}

export default function ServiceGridSection({ data }: { data: ClientData }) {
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });
  const titles = data.sectionTitles || {};
  const title = titles.services || "Serviços";
  const subtitle = titles.servicesSubtitle || "Conheça nossos serviços";
  const description = (titles as Record<string, string>).servicesDescription || "";
  const serviceItems = data.serviceItems || data.services.map((s) => ({
    title: s,
    description: "",
    icon: "Sparkles",
  }));

  if (serviceItems.length === 0) return null;

  return (
    <section id="servicos" className="py-20 md:py-32 bg-white" ref={sectionRef}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="max-w-2xl mb-12 md:mb-16"
        >
          <span className="text-sm font-semibold text-primary uppercase tracking-wider">{title}</span>
          <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900">
            {subtitle}
          </h2>
          {description && (
            <p className="mt-4 text-base md:text-lg text-muted leading-relaxed">{description}</p>
          )}
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {serviceItems.map((item, i) => (
            <ServiceCard
              key={item.title}
              item={item}
              index={i}
              colorClass={i % 2 === 0 ? "bg-primary/10 text-primary" : "bg-accent/10 text-accent"}
            />
          ))}
        </div>
      </div>
    </section>
  );
}