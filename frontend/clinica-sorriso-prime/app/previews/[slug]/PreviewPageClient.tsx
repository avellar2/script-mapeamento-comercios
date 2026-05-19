"use client";

import type { ClientData } from "@/types/client";
import TemplateRenderer from "@/components/templates/TemplateRenderer";

export default function PreviewPageClient({ data }: { data: ClientData }) {
  return (
    <div className="min-h-full flex flex-col bg-white text-slate-900">
      <TemplateRenderer data={data} />
    </div>
  );
}