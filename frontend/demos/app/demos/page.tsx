"use client";

import { motion } from "framer-motion";
import { demos } from "@/lib/demo-data";
import { Layers, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function DemosIndexPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Hero */}
      <section className="relative px-5 pt-16 pb-12">
        <div className="max-w-xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 border border-slate-200 px-3 py-1 text-xs font-bold text-slate-600 mb-5">
              <Layers size={12} /> Demo Library
            </span>
            <h1 className="text-3xl md:text-4xl font-black text-slate-900 leading-tight">
              Landing pages prontas{" "}
              <span className="text-indigo-600">para vender</span>
            </h1>
            <p className="mt-4 text-base text-slate-600 leading-relaxed">
              Biblioteca de demos por nicho. Mini sites, paginas de WhatsApp, agendamento e catalogos digitais.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Grid */}
      <section className="px-5 pb-20">
        <div className="max-w-xl mx-auto grid gap-5">
          {demos.map((demo, i) => (
            <motion.div
              key={demo.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
            >
              <Link
                href={`/demos/${demo.slug}`}
                className="group block rounded-2xl border border-slate-200 bg-white overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="h-32 md:h-40 flex items-center justify-center relative overflow-hidden" style={{ backgroundColor: demo.bgColor }}>
                  <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-black to-transparent" />
                  <motion.div
                    className="text-4xl font-black tracking-tighter"
                    style={{ color: demo.accentColor }}
                    whileHover={{ scale: 1.05 }}
                  >
                    {demo.name.charAt(0)}
                  </motion.div>
                </div>

                <div className="p-5">
                  <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: demo.accentColor }}>
                    {demo.category}
                  </span>
                  <h3 className="mt-1 text-lg font-extrabold text-slate-900 leading-tight">{demo.name}</h3>
                  <p className="mt-2 text-sm text-slate-600 leading-relaxed line-clamp-2">{demo.description}</p>

                  <div className="mt-4 inline-flex items-center gap-1 text-sm font-bold transition-colors hover:underline" style={{ color: demo.accentColor }}>
                    Ver demo
                    <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
