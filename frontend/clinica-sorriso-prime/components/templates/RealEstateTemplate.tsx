"use client";

import type { ClientData } from "@/types/client";
import NavigationSection from "@/components/sections/NavigationSection";
import HeroSection from "@/components/sections/HeroSection";
import ServiceGridSection from "@/components/sections/ServiceGridSection";
import DifferentialsSection from "@/components/sections/DifferentialsSection";
import TestimonialsSection from "@/components/sections/TestimonialsSection";
import LocationSection from "@/components/sections/LocationSection";
import FooterCTASection from "@/components/sections/FooterCTASection";
import FooterSection from "@/components/sections/FooterSection";
import FloatingWhatsAppButton from "@/components/sections/FloatingWhatsAppButton";

export default function RealEstateTemplate({ data }: { data: ClientData }) {
  return (
    <>
      <NavigationSection data={data} />
      <main className="flex-1">
        <HeroSection data={data} />
        <ServiceGridSection data={data} />
        <DifferentialsSection data={data} />
        <TestimonialsSection data={data} />
        <LocationSection data={data} />
        <FooterCTASection data={data} />
      </main>
      <FooterSection data={data} />
      <FloatingWhatsAppButton data={data} />
    </>
  );
}