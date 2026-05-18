"use client";

interface LiquidGlassProps {
  children: React.ReactNode;
  className?: string;
}

export function LiquidGlass({ children, className = "" }: LiquidGlassProps) {
  return (
    <div
      className={`relative rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_20px_40px_-15px_rgba(0,0,0,0.3)] overflow-hidden ${className}`}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] to-transparent pointer-events-none" />
      {children}
    </div>
  );
}
