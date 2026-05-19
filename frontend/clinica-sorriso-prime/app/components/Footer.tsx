"use client";

export default function Footer() {
  return (
    <footer className="py-10 md:py-14 bg-slate-900 text-slate-400">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2C8 2 5 5 5 9c0 3 2 5 2 8 0 2 1 3 2 3s2-1 2-3c0-1 0-2 1-2s1 1 1 2c0 2 1 3 2 3s2-1 2-3c0-3 2-5 2-8 0-4-3-7-7-7z"/>
              </svg>
            </div>
            <span className="text-white font-semibold">Sorriso Prime</span>
          </div>

          <div className="flex flex-col md:flex-row gap-4 md:gap-8 text-sm">
            <a href="#tratamentos" className="hover:text-white transition-colors">Tratamentos</a>
            <a href="#equipe" className="hover:text-white transition-colors">Equipe</a>
            <a href="#localizacao" className="hover:text-white transition-colors">Localização</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
          </div>

          <div className="text-xs text-slate-500">
            © 2024 Clínica Sorriso Prime · Todos os direitos reservados
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 text-xs text-slate-500 text-center md:text-left">
          <p>
            Clínica fictícia criada para fins demonstrativos. Não realiza atendimentos reais.
          </p>
        </div>
      </div>
    </footer>
  );
}
