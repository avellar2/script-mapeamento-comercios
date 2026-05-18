"use client";

import { motion } from "framer-motion";
import { Phone } from "lucide-react";
import { buildWhatsAppLink, defaultMessage } from "@/lib/whatsapp";

interface DemoLayoutProps {
  children: React.ReactNode;
  name: string;
  phone: string;
  accentColor: string;
  textColor: string;
  bgColor: string;
  whatsappLabel: string;
}

export function DemoLayout({
  children,
  name,
  phone,
  accentColor,
  textColor,
  bgColor,
  whatsappLabel,
}: DemoLayoutProps) {
  const waLink = buildWhatsAppLink(phone, defaultMessage(name));

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: bgColor, color: textColor }}
    >
      {children}

      <a
        href={waLink}
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full px-5 py-3 shadow-lg transition-transform hover:scale-105 active:scale-95"
        style={{ backgroundColor: accentColor, color: "#ffffff" }}
      >
        <Phone size={18} />
        <span className="text-sm font-semibold">{whatsappLabel}</span>
      </a>
    </div>
  );
}
