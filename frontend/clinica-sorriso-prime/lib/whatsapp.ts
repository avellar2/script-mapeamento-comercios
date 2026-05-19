export function createWhatsAppLink(phone: string, businessName: string): string {
  const cleanPhone = phone.replace(/\D/g, "");
  const message = encodeURIComponent(
    `Olá, vim pela página e gostaria de mais informações sobre ${businessName}.`
  );
  return `https://wa.me/${cleanPhone}?text=${message}`;
}

export function formatPhoneDisplay(phone: string): string {
  const clean = phone.replace(/\D/g, "");
  if (clean.length === 13) {
    return `(${clean.slice(2, 4)}) ${clean.slice(4, 9)}-${clean.slice(9)}`;
  }
  if (clean.length === 11) {
    return `(${clean.slice(0, 2)}) ${clean.slice(2, 7)}-${clean.slice(7)}`;
  }
  return phone;
}