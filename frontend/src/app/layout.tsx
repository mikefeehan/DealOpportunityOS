import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "OpportunityOS Tucson | InTrust",
  description: "Internal acquisition intelligence platform for InTrust Property Group."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
