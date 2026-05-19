"use client";

import type { ClientData } from "@/types/client";

export default function FooterSection({ data }: { data: ClientData }) {
  const navLinks = data.navLinks || [
    { href: "#servicos", label: "Serviços" },
    { href: "#localizacao", label: "Localização" },
    { href: "#faq", label: "FAQ" },
  ];

  return (
    <footer className="py-10 md:py-14 bg-slate-900 text-slate-400">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              {data.logoSvg ? (
                <div dangerouslySetInnerHTML={{ __html: data.logoSvg }} />
              ) : (
                <span className="text-white text-sm font-bold">
                  {data.businessName.charAt(0)}
                </span>
              )}
            </div>
            <span className="text-white font-semibold">{data.businessName}</span>
          </div>

          <div className="flex flex-col md:flex-row gap-4 md:gap-8 text-sm">
            {navLinks.map((link) => (
              <a key={link.href} href={link.href} className="hover:text-white transition-colors">
                {link.label}
              </a>
            ))}
          </div>

          <div className="text-xs text-slate-500">
            © {new Date().getFullYear()} {data.businessName} · Todos os direitos reservados
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 text-xs text-slate-500 text-center md:text-left">
          <p>{data.notes || `Página profissional de ${data.businessName}.`}</p>
        </div>
      </div>
    </footer>
  );
}