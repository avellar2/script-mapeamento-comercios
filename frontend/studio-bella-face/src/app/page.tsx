import { Hero } from "@/components/hero";
import { Services } from "@/components/services";
import { Differentials } from "@/components/differentials";
import { Gallery } from "@/components/gallery";
import { Testimonials } from "@/components/testimonials";
import { Location } from "@/components/location";
import { FinalCTA } from "@/components/final-cta";
import { Footer } from "@/components/footer";
import { FloatingWhatsApp } from "@/components/floating-whatsapp";

export default function Home() {
  return (
    <>
      <Hero />
      <Services />
      <Differentials />
      <Gallery />
      <Testimonials />
      <Location />
      <FinalCTA />
      <Footer />
      <FloatingWhatsApp />
    </>
  );
}
