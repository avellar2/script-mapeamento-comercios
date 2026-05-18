"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Phone } from "lucide-react";
import { buildWhatsAppLink, defaultMessage } from "@/lib/whatsapp";

interface MagneticButtonProps {
  phone: string;
  label: string;
  businessName: string;
  accentColor: string;
  fullWidth?: boolean;
}

export function MagneticButton({
  phone,
  label,
  businessName,
  accentColor,
  fullWidth = false,
}: MagneticButtonProps) {
  const ref = useRef<HTMLAnchorElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const link = buildWhatsAppLink(phone, defaultMessage(businessName));

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const distX = e.clientX - centerX;
    const distY = e.clientY - centerY;
    setPosition({ x: distX * 0.15, y: distY * 0.15 });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.a
      ref={ref}
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      className={`relative inline-flex items-center justify-center gap-2 rounded-full px-8 py-4 text-sm font-bold text-white shadow-[0_8px_32px_-8px_rgba(0,0,0,0.3)] overflow-hidden ${fullWidth ? "w-full" : ""}`}
      style={{ backgroundColor: accentColor }}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: "spring", stiffness: 150, damping: 15, mass: 0.1 }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.97 }}
    >
      <span className="absolute inset-0 bg-white/10 translate-y-full hover:translate-y-0 transition-transform duration-300 ease-out" />
      <Phone size={18} strokeWidth={2.5} />
      <span className="relative z-10">{label}</span>
    </motion.a>
  );
}
