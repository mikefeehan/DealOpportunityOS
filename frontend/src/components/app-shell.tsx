"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, Download, FileText, Flame, LayoutGrid, ListChecks, MapPin, PhoneCall, Radar, RefreshCw, TrendingUp, UploadCloud, Users } from "lucide-react";
import { ReactNode, useEffect, useState } from "react";
import { scanTucson, exportUrl, getMarkets, getSelectedMarket, getSummary, setSelectedMarket } from "@/lib/api";
import type { MarketOption } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const nav = [
  { href: "/", label: "Top Owners", icon: PhoneCall },
  { href: "/command-center", label: "Command Center", icon: BarChart3 },
  { href: "/opportunities", label: "Opportunity Finder", icon: Radar },
  { href: "/deals", label: "Deal Finder", icon: LayoutGrid },
  { href: "/rent-gap", label: "Rent-Gap Candidates", icon: TrendingUp },
  { href: "/debt", label: "Maturing Debt", icon: Flame },
  { href: "/owners", label: "Owner Intelligence", icon: Users },
  { href: "/map", label: "Market Map", icon: MapPin },
  { href: "/pipeline", label: "Pipeline", icon: ListChecks },
  { href: "/review", label: "Import & Review", icon: UploadCloud }
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
  const [markets, setMarkets] = useState<MarketOption[]>([]);
  const [market, setMarket] = useState("");

  useEffect(() => {
    getSummary().then((summary) => setProvenance(summary.data_provenance));
    getMarkets().then(setMarkets);
    setMarket(getSelectedMarket());
  }, []);

  function changeMarket(value: string) {
    setMarket(value);
    setSelectedMarket(value);
    router.refresh();
    window.location.reload();
  }

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
        <div className="border-b border-border pb-4">
          <Link href="/" className="block">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/brand/intrust-white.png" alt="InTrust Property Group" className="h-auto w-44" />
          </Link>
          <div className="mt-2 text-[10px] uppercase tracking-[0.18em] text-muted">
            OpportunityOS · Acquisition Intelligence
          </div>
        </div>
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
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {markets.length > 0 && (
                <select
                  value={market}
                  onChange={(e) => changeMarket(e.target.value)}
                  className="h-9 rounded-md border border-border bg-panel2 px-2 text-sm text-ink outline-none focus:border-amber/60"
                  title="Filter by market"
                >
                  <option value="">All markets</option>
                  {markets.map((m) => (
                    <option key={m.market} value={m.market}>
                      {m.market} ({m.properties})
                    </option>
                  ))}
                </select>
              )}
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
