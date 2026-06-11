import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

// Brand fonts: Futura (Md BT Medium) for UI/body, Bronova for display/headings.
const futura = localFont({
  src: "../fonts/futura-medium.ttf",
  variable: "--font-sans",
  display: "swap"
});

const bronova = localFont({
  src: [
    { path: "../fonts/bronova-regular.otf", weight: "400", style: "normal" },
    { path: "../fonts/bronova-bold.ttf", weight: "700", style: "normal" }
  ],
  variable: "--font-display",
  display: "swap"
});

export const metadata: Metadata = {
  title: "OpportunityOS | InTrust Property Group",
  description: "Internal acquisition intelligence platform for InTrust Property Group."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${futura.variable} ${bronova.variable}`}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
