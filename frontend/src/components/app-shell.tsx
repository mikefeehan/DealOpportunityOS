"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, Building2, Download, FileText, ListChecks, PhoneCall, Radar, RefreshCw, Users } from "lucide-react";
import { ReactNode, useEffect, useState } from "react";
import { scanTucson, exportUrl, getSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const nav = [
  { href: "/", label: "Top Owners", icon: PhoneCall },
  { href: "/command-center", label: "Command Center", icon: BarChart3 },
  { href: "/opportunities", label: "Opportunity Finder", icon: Radar },
  { href: "/owners", label: "Owner Intelligence", icon: Users },
  { href: "/pipeline", label: "Pipeline", icon: ListChecks }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [scanLabel, setScanLabel] = useState("Tucson Scan");
  const [scanning, setScanning] = useState(false);
  const [provenance, setProvenance] = useState<{
    mode: string;
    live_records: number;
    fallback_records: number;
    disclaimer: string;
  } | null>(null);

  useEffect(() => {
    getSummary().then((summary) => setProvenance(summary.data_provenance));
  }, []);

  async function runScan() {
    setScanning(true);
    setScanLabel("Scanning");
    const result = await scanTucson();
    setScanLabel(result.live_records_imported > 0 ? "Live Scan Loaded" : "Fallback Active");
    getSummary().then((summary) => setProvenance(summary.data_provenance));
    setScanning(false);
    router.refresh();
    window.setTimeout(() => setScanLabel("Tucson Scan"), 2200);
  }

  return (
    <div className="min-h-screen bg-background terminal-grid">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-border bg-[#090909]/95 p-4 backdrop-blur lg:block">
        <Link href="/" className="flex items-center gap-3 border-b border-border pb-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-md border border-amber/40 bg-amber/10 text-amber">
            <Building2 size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold text-ink">InTrust</div>
            <div className="text-xs uppercase text-muted">OpportunityOS Tucson</div>
          </div>
        </Link>
        <nav className="mt-5 space-y-1">
          {nav.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted transition-colors hover:bg-panel2 hover:text-ink",
                  active && "bg-panel2 text-amber"
                )}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-4 right-4 rounded-lg border border-border bg-panel p-3">
          <div className="text-xs uppercase text-muted">Decision Rule</div>
          <div className="mt-1 text-sm text-ink">Call Score = 50% Fit + 50% Motivation</div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-border bg-[#090909]/92 backdrop-blur">
          <div className="flex min-h-16 flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between lg:px-6">
            <div>
              <div className="text-xs uppercase text-muted">Internal acquisition intelligence</div>
              <div className="text-lg font-semibold text-ink">Who should InTrust call this week?</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="secondary" onClick={runScan} disabled={scanning}>
                <RefreshCw size={15} className={scanning ? "animate-spin" : ""} />
                {scanLabel}
              </Button>
              <Button asChild variant="secondary">
                <a href={exportUrl("/api/export/csv")}>
                  <Download size={15} />
                  CSV
                </a>
              </Button>
              <Button asChild>
                <a href={exportUrl("/api/export/today-call-list.pdf")}>
                  <FileText size={15} />
                  Call List PDF
                </a>
              </Button>
            </div>
          </div>
          {provenance && provenance.fallback_records > 0 && (
            <div className="border-t border-amber/20 bg-amber/10 px-4 py-2 text-xs text-amber lg:px-6">
              Data mode: {provenance.mode}. Live records: {provenance.live_records}. Fallback records:{" "}
              {provenance.fallback_records}. {provenance.disclaimer}
            </div>
          )}
          <div className="flex gap-1 overflow-x-auto border-t border-border px-3 py-2 lg:hidden">
            {nav.map((item) => {
              const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex h-9 shrink-0 items-center gap-2 rounded-md px-3 text-xs text-muted",
                    active && "bg-panel2 text-amber"
                  )}
                >
                  <Icon size={14} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </header>
        <main className="px-4 py-5 lg:px-6">{children}</main>
      </div>
    </div>
  );
}
