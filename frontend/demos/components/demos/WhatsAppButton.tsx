"use client";

import { Phone } from "lucide-react";
import { motion } from "framer-motion";
import { buildWhatsAppLink, defaultMessage } from "@/lib/whatsapp";

interface WhatsAppButtonProps {
  phone: string;
  label: string;
  businessName: string;
  variant?: "filled" | "outline";
  accentColor: string;
  fullWidth?: boolean;
}

export function WhatsAppButton({
  phone,
  label,
  businessName,
  variant = "filled",
  accentColor,
  fullWidth = false,
}: WhatsAppButtonProps) {
  const link = buildWhatsAppLink(phone, defaultMessage(businessName));

  const base = "inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-bold transition-transform hover:scale-105 active:scale-95";
  const filled = "text-white shadow-lg";
  const outline = "border-2 bg-transparent";

  const classes = `${base} ${variant === "filled" ? filled : outline} ${fullWidth ? "w-full" : ""}`;

  return (
    <motion.a
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      className={classes}
      style={variant === "filled" ? { backgroundColor: accentColor } : { borderColor: accentColor, color: accentColor }}
      whileTap={{ scale: 0.97 }}
    >
      <Phone size={18} />
      {label}
    </motion.a>
  );
}
