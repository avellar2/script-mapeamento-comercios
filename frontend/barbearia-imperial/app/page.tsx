import { Hero } from "@/app/components/hero";
import { Services } from "@/app/components/services";
import { Gallery } from "@/app/components/gallery";
import { Differentials } from "@/app/components/differentials";
import { Testimonials } from "@/app/components/testimonials";
import { Location } from "@/app/components/location";
import { FinalCTA } from "@/app/components/final-cta";
import { Footer } from "@/app/components/footer";
import { FloatingWhatsApp } from "@/app/components/floating-whatsapp";

export default function Home() {
  return (
    <>
      <Hero />
      <Services />
      <Gallery />
      <Differentials />
      <Testimonials />
      <Location />
      <FinalCTA />
      <Footer />
      <FloatingWhatsApp />
    </>
  );
}
