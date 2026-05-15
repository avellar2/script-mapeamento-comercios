"use client";

import { InstagramLogo, FacebookLogo } from "@phosphor-icons/react";

export function Footer() {
  return (
    <footer className="w-full border-t-4 border-wood bg-surface py-12">
      <div className="mx-auto flex max-w-[1400px] flex-col items-center justify-between gap-6 px-6 md:flex-row md:px-12 lg:px-20">
        <div className="flex flex-col items-center gap-2 md:items-start">
          <p className="text-xl font-black tracking-tight text-wood">
            Abrasileirado
          </p>
          <p className="text-sm text-text-muted">
            Comida de verdade desde 2018.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <a
            href="#"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white transition-colors hover:bg-accent-dark"
            aria-label="Instagram"
          >
            <InstagramLogo size={20} weight="fill" />
          </a>
          <a
            href="#"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white transition-colors hover:bg-accent-dark"
            aria-label="Facebook"
          >
            <FacebookLogo size={20} weight="fill" />
          </a>
        </div>

        <p className="text-xs text-text-muted">
          © 2024 Abrasileirado. Todos os direitos reservados.
        </p>
      </div>
    </footer>
  );
}
