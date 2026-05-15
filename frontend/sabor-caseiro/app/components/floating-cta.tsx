"use client";

import { motion } from "framer-motion";
import { WhatsappLogo } from "@phosphor-icons/react";

export function FloatingCTA() {
  return (
    <motion.a
      href="https://wa.me/5511999999999?text=Ol%C3%A1%21%20Gostaria%20de%20fazer%20um%20pedido."
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[#25d366] text-white shadow-lg transition-transform duration-150 ease-out hover:scale-110 active:scale-95"
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 15, delay: 2 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      aria-label="Pedir pelo WhatsApp"
    >
      <WhatsappLogo size={28} weight="fill" />
    </motion.a>
  );
}
