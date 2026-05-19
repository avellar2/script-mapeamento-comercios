import type { Metadata } from "next";
import { getClientData, getAllClientSlugs } from "@/lib/clients";
import PreviewPageClient from "./PreviewPageClient";

interface PreviewPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PreviewPageProps): Promise<Metadata> {
  const { slug } = await params;
  const data = getClientData(slug);

  if (!data) {
    return { title: "Página não encontrada" };
  }

  return {
    title: `${data.businessName} | Landing Page`,
    description: data.subheadline,
  };
}

export function generateStaticParams() {
  return getAllClientSlugs().map((slug) => ({ slug }));
}

export default async function PreviewPage({ params }: PreviewPageProps) {
  const { slug } = await params;
  const data = getClientData(slug);

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Cliente não encontrado</h1>
          <p className="text-muted">
            Nenhum cliente com o slug &ldquo;{slug}&rdquo; foi encontrado em data/clients/.
          </p>
        </div>
      </div>
    );
  }

  return <PreviewPageClient data={data} />;
}