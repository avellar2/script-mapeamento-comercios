import Navigation from "./components/Navigation";
import Hero from "./components/Hero";
import Treatments from "./components/Treatments";
import Differentials from "./components/Differentials";
import Team from "./components/Team";
import Testimonials from "./components/Testimonials";
import Structure from "./components/Structure";
import Location from "./components/Location";
import FAQ from "./components/FAQ";
import FooterCTA from "./components/FooterCTA";
import Footer from "./components/Footer";
import FloatingWhatsApp from "./components/FloatingWhatsApp";

export default function Home() {
  return (
    <>
      <Navigation />
      <main className="flex-1">
        <Hero />
        <Treatments />
        <Differentials />
        <Team />
        <Testimonials />
        <Structure />
        <Location />
        <FAQ />
        <FooterCTA />
      </main>
      <Footer />
      <FloatingWhatsApp />
    </>
  );
}
