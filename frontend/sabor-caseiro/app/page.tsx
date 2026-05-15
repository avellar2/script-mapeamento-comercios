import { Hero } from "@/app/components/hero";
import { Dishes } from "@/app/components/dishes";
import { Combos } from "@/app/components/combos";
import { Menu } from "@/app/components/menu";
import { Testimonials } from "@/app/components/testimonials";
import { Location } from "@/app/components/location";
import { FinalCTA } from "@/app/components/final-cta";
import { Footer } from "@/app/components/footer";
import { FloatingCTA } from "@/app/components/floating-cta";

export default function Home() {
  return (
    <>
      <Hero />
      <Dishes />
      <Combos />
      <Menu />
      <Testimonials />
      <Location />
      <FinalCTA />
      <Footer />
      <FloatingCTA />
    </>
  );
}
