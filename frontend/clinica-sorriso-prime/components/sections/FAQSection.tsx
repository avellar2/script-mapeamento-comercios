"use client";

import { useState, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import type { ClientData, FAQItem } from "@/types/client";

function FAQItemComponent({ faq, index }: { faq: FAQItem; index: number }) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ type: "spring", stiffness: 100, damping: 20, delay: index * 0.06 }}
      className="border-b border-border last:border-0"
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-4 py-5 md:py-6 text-left group"
      >
        <span className="text-base md:text-lg font-medium text-slate-900 group-hover:text-primary transition-colors">
          {faq.question}
        </span>
        <div
          className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 ${
            isOpen ? "bg-primary text-white" : "bg-surface text-slate-500"
          }`}
        >
          {isOpen ? <Minus size={16} /> : <Plus size={16} />}
        </div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="overflow-hidden"
          >
            <p className="pb-5 md:pb-6 text-sm md:text-base text-muted leading-relaxed max-w-[65ch]">
              {faq.answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function FAQSection({ data }: { data: ClientData }) {
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });
  const titles = data.sectionTitles || {};
  const title = titles.faq || "Perguntas frequentes";
  const subtitle = titles.faqSubtitle || "Perguntas frequentes";
  const description = (titles as Record<string, string>).faqDescription || "";
  const faqs = data.faq || [];

  if (faqs.length === 0) return null;

  return (
    <section id="faq" className="py-20 md:py-32 bg-white" ref={sectionRef}>
      <div className="max-w-[900px] mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="text-center mb-12 md:mb-16"
        >
          <span className="text-sm font-semibold text-primary uppercase tracking-wider">{title}</span>
          <h2 className="mt-3 text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900">
            {subtitle}
          </h2>
          {description && (
            <p className="mt-4 text-base md:text-lg text-muted leading-relaxed">{description}</p>
          )}
        </motion.div>

        <div className="bg-surface rounded-[1.5rem] p-4 md:p-8 border border-border">
          {faqs.map((faq: FAQItem, i: number) => (
            <FAQItemComponent key={i} faq={faq} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}