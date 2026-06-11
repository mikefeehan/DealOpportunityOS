import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMoney(value: number | undefined, compact = true) {
  const amount = value ?? 0;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: compact ? "compact" : "standard",
    maximumFractionDigits: compact ? 1 : 0
  }).format(amount);
}

export function formatNumber(value: number | undefined) {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

export function ownerHref(owner: string) {
  return `/owners/${encodeURIComponent(owner)}`;
}
