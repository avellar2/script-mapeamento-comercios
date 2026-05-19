export type TemplateName =
  | "advogado"
  | "dentista"
  | "estetica"
  | "barbearia"
  | "cardapio"
  | "assistencia-tecnica"
  | "igreja-evento"
  | "imobiliaria"
  | "automotiva"
  | "cursos"
  | "personalizado";

export interface NavLink {
  href: string;
  label: string;
}

export interface TeamMember {
  name: string;
  role: string;
  specialty?: string;
  image: string;
  credential?: string;
}

export interface Testimonial {
  name: string;
  role: string;
  text: string;
  rating: number;
  image: string;
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface ServiceItem {
  icon?: string;
  title: string;
  description: string;
}

export interface DifferentialItem {
  icon?: string;
  title: string;
  description: string;
}

export interface BrandColors {
  primary: string;
  primaryLight?: string;
  primaryDark?: string;
  secondary: string;
  accent: string;
}

export interface SectionTitles {
  services?: string;
  servicesSubtitle?: string;
  differentials?: string;
  differentialsSubtitle?: string;
  team?: string;
  teamSubtitle?: string;
  testimonials?: string;
  testimonialsSubtitle?: string;
  structure?: string;
  structureSubtitle?: string;
  location?: string;
  locationSubtitle?: string;
  faq?: string;
  faqSubtitle?: string;
  cta?: string;
  ctaSubtitle?: string;
}

export interface ClientData {
  slug: string;
  template: TemplateName;
  businessName: string;
  headline: string;
  subheadline: string;
  whatsapp: string;
  city: string;
  neighborhood?: string;
  address: string;
  instagram?: string;
  googleMapsUrl?: string;
  rating?: string;
  reviewsCount?: string;
  services: string[];
  differentials: string[];
  images: {
    hero?: string[];
    gallery?: string[];
    team?: string[];
    structure?: string[];
  };
  brandColors: BrandColors;
  notes?: string;
  team?: TeamMember[];
  testimonials?: Testimonial[];
  faq?: FAQItem[];
  navLinks?: NavLink[];
  trustSignals?: string[];
  ctaLabel?: string;
  ctaText?: string;
  sectionTitles?: SectionTitles;
  openingHours?: string;
  phone?: string;
  email?: string;
  serviceItems?: ServiceItem[];
  differentialItems?: DifferentialItem[];
  logoSvg?: string;
}