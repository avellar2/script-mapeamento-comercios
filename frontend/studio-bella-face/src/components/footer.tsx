export function Footer() {
  return (
    <footer className="w-full border-t border-border-custom bg-background px-6 py-10 md:px-12 lg:px-20">
      <div className="mx-auto flex max-w-[1400px] flex-col items-center justify-between gap-4 md:flex-row">
        <p className="text-sm text-text-muted">
          © 2025 Studio Bella Face. Todos os direitos reservados.
        </p>
        <div className="flex gap-6">
          <a
            href="#"
            className="text-sm text-text-muted transition-colors duration-200 hover:text-accent"
          >
            Instagram
          </a>
          <a
            href="#"
            className="text-sm text-text-muted transition-colors duration-200 hover:text-accent"
          >
            Política de Privacidade
          </a>
        </div>
      </div>
    </footer>
  );
}
