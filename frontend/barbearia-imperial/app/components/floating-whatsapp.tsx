"use client";

import { motion } from "framer-motion";
import { ChatCircleText } from "@phosphor-icons/react";

export const FloatingWhatsApp = () => {
  return (
    <motion.a
      href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20agendar%20um%20corte."
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-[#25D366] px-5 py-3.5 text-sm font-semibold text-white shadow-[0_12px_32px_-8px_rgba(37,211,102,0.4)] transition-transform duration-150 ease-out active:scale-[0.97] md:bottom-8 md:right-8"
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ delay: 1.2, type: "spring", stiffness: 200, damping: 15 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      aria-label="Agendar pelo WhatsApp"
    >
      <motion.span
        animate={{ scale: [1, 1.15, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        <ChatCircleText size={22} weight="fill" />
      </motion.span>
      <span className="hidden md:inline">Agendar</span>
    </motion.a>
  );
};
