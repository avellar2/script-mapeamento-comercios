"use client";

import type { ClientData, TemplateName } from "@/types/client";
import DentistTemplate from "./DentistTemplate";
import LawyerTemplate from "./LawyerTemplate";
import BeautyTemplate from "./BeautyTemplate";
import BarberTemplate from "./BarberTemplate";
import FoodTemplate from "./FoodTemplate";
import TechnicalServiceTemplate from "./TechnicalServiceTemplate";
import ChurchEventTemplate from "./ChurchEventTemplate";
import RealEstateTemplate from "./RealEstateTemplate";
import AutoTemplate from "./AutoTemplate";
import CourseTemplate from "./CourseTemplate";
import CustomProductsTemplate from "./CustomProductsTemplate";
import ThemeWrapper from "@/components/sections/ThemeWrapper";

const templates: Record<TemplateName, React.ComponentType<{ data: ClientData }>> = {
  dentista: DentistTemplate,
  advogado: LawyerTemplate,
  estetica: BeautyTemplate,
  barbearia: BarberTemplate,
  cardapio: FoodTemplate,
  "assistencia-tecnica": TechnicalServiceTemplate,
  "igreja-evento": ChurchEventTemplate,
  imobiliaria: RealEstateTemplate,
  automotiva: AutoTemplate,
  cursos: CourseTemplate,
  personalizado: CustomProductsTemplate,
};

export default function TemplateRenderer({ data }: { data: ClientData }) {
  const TemplateComponent = templates[data.template];

  if (!TemplateComponent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Template não encontrado</h1>
          <p className="text-muted">
            O template &ldquo;{data.template}&rdquo; não está disponível. Templates disponíveis: {Object.keys(templates).join(", ")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <ThemeWrapper data={data}>
      <TemplateComponent data={data} />
    </ThemeWrapper>
  );
}