export function buildWhatsAppLink(phone: string, message?: string): string {
  const cleaned = phone.replace(/\D/g, "");
  const text = message ? `?text=${encodeURIComponent(message)}` : "";
  return `https://wa.me/${cleaned}${text}`;
}

export const defaultMessage = (business: string) =>
  `Olá! Vi a página da ${business} e gostaria de saber mais.`;
