"use client";

import type { ClientData } from "@/types/client";

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

function lighten(hex: string, amount: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  const r = Math.min(255, rgb.r + (255 - rgb.r) * amount);
  const g = Math.min(255, rgb.g + (255 - rgb.g) * amount);
  const b = Math.min(255, rgb.b + (255 - rgb.b) * amount);
  return `#${Math.round(r).toString(16).padStart(2, "0")}${Math.round(g).toString(16).padStart(2, "0")}${Math.round(b).toString(16).padStart(2, "0")}`;
}

function darken(hex: string, amount: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  const r = Math.max(0, rgb.r * (1 - amount));
  const g = Math.max(0, rgb.g * (1 - amount));
  const b = Math.max(0, rgb.b * (1 - amount));
  return `#${Math.round(r).toString(16).padStart(2, "0")}${Math.round(g).toString(16).padStart(2, "0")}${Math.round(b).toString(16).padStart(2, "0")}`;
}

function withAlpha(hex: string, alpha: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

export default function ThemeWrapper({
  data,
  children,
}: {
  data: ClientData;
  children: React.ReactNode;
}) {
  const { brandColors } = data;
  const primary = brandColors.primary;
  const primaryLight = brandColors.primaryLight || lighten(primary, 0.7);
  const primaryDark = brandColors.primaryDark || darken(primary, 0.2);

  const style: React.CSSProperties = {
    "--color-primary": primary,
    "--color-primary-light": primaryLight,
    "--color-primary-dark": primaryDark,
    "--color-accent": brandColors.accent,
    "--color-accent-light": lighten(brandColors.accent, 0.7),
  } as React.CSSProperties;

  return (
    <div style={style} data-template={data.template} data-slug={data.slug}>
      <style>{`
        [data-template] .bg-primary\\/10 { background-color: ${withAlpha(primary, 0.1)}; }
        [data-template] .text-primary { color: ${primary}; }
        [data-template] .bg-primary { background-color: ${primary}; }
        [data-template] .hover\\:bg-primary-dark:hover { background-color: ${primaryDark}; }
        [data-template] .hover\\:text-primary:hover { color: ${primary}; }
        [data-template] .hover\\:border-primary\\/20:hover { border-color: ${withAlpha(primary, 0.2)}; }
        [data-template] .hover\\:border-primary\\/30:hover { border-color: ${withAlpha(primary, 0.3)}; }
        [data-template] .border-primary\\/20 { border-color: ${withAlpha(primary, 0.2)}; }
        [data-template] .group-hover\\:bg-primary { background-color: ${primary}; }
        [data-template] .group-hover\\:text-white { color: white; }
        [data-template] .group-hover\\:text-primary { color: ${primary}; }
      `}</style>
      {children}
    </div>
  );
}