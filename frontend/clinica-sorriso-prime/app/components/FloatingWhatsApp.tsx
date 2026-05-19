"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Phone, X } from "lucide-react";

export default function FloatingWhatsApp() {
  const [isVisible, setIsVisible] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsVisible(window.scrollY > 400);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => setShowTooltip(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setShowTooltip(false);
    }
  }, [isVisible]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: 20 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
          className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3"
        >
          <AnimatePresence>
            {showTooltip && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.9 }}
                className="bg-white rounded-xl p-3 shadow-[0_8px_30px_rgba(0,0,0,0.12)] border border-border max-w-[220px] relative"
              >
                <button
                  onClick={() => setShowTooltip(false)}
                  className="absolute top-1.5 right-1.5 p-0.5 text-slate-400 hover:text-slate-600"
                >
                  <X size={12} />
                </button>
                <p className="text-xs text-slate-600 pr-4">
                  Olá! Quer agendar sua avaliação? Clique aqui.
                </p>
                <div className="absolute -bottom-2 right-5 w-3 h-3 bg-white border-r border-b border-border rotate-45" />
              </motion.div>
            )}
          </AnimatePresence>

          <a
            href="https://wa.me/5511999999999?text=Olá!%20Gostaria%20de%20agendar%20uma%20avaliação."
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center justify-center w-14 h-14 bg-[#25D366] text-white rounded-full shadow-[0_4px_20px_rgba(37,211,102,0.4)] hover:shadow-[0_6px_30px_rgba(37,211,102,0.5)] transition-all active:scale-[0.95]"
            aria-label="Agendar pelo WhatsApp"
          >
            <Phone size={24} strokeWidth={2} className="group-hover:rotate-12 transition-transform" />
          </a>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
