"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Award, BookOpen } from "lucide-react";
import type { ClientData, TeamMember } from "@/types/client";

export default function TeamSection({ data }: { data: ClientData }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const titles = data.sectionTitles || {};
  const title = titles.team || "Nossa Equipe";
  const subtitle = titles.teamSubtitle || "Quem cuida de você";
  const description = (titles as Record<string, string>).teamDescription || "";
  const team = data.team || [];

  if (team.length === 0) return null;

  return (
    <section id="equipe" className="py-20 md:py-32 bg-white" ref={ref}>
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {team.map((member: TeamMember, i: number) => (
            <motion.div
              key={member.name}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: "spring", stiffness: 100, damping: 20, delay: i * 0.12 }}
              className="group"
            >
              <div className="relative overflow-hidden rounded-[1.5rem] bg-surface aspect-[3/4] mb-5">
                <img
                  src={member.image}
                  alt={member.name}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                {member.credential && (
                  <div className="absolute bottom-4 left-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 translate-y-2 group-hover:translate-y-0">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-white/90 backdrop-blur-sm rounded-lg text-xs font-medium text-slate-700">
                      <Award size={12} />
                      {member.credential}
                    </span>
                  </div>
                )}
              </div>
              <h3 className="text-lg font-semibold text-slate-900">{member.name}</h3>
              <p className="text-sm font-medium text-primary mt-0.5">{member.role}</p>
              {member.specialty && (
                <p className="text-sm text-muted mt-1.5 flex items-center gap-1.5">
                  <BookOpen size={14} />
                  {member.specialty}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}