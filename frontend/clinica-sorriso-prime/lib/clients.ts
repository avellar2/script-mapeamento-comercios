import fs from "fs";
import path from "path";
import type { ClientData } from "@/types/client";

const clientsDir = path.join(process.cwd(), "data", "clients");

export function getAllClientSlugs(): string[] {
  try {
    const files = fs.readdirSync(clientsDir);
    return files
      .filter((f) => f.endsWith(".json"))
      .map((f) => f.replace(/\.json$/, ""));
  } catch {
    return [];
  }
}

export function getClientData(slug: string): ClientData | null {
  try {
    const filePath = path.join(clientsDir, `${slug}.json`);
    const raw = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(raw) as ClientData;
  } catch {
    return null;
  }
}

export function getAllClients(): ClientData[] {
  const slugs = getAllClientSlugs();
  return slugs
    .map((slug) => getClientData(slug))
    .filter((c): c is ClientData => c !== null);
}