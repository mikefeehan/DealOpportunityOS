"use client";

import Link from "next/link";
import { ArrowUpDown, Building2, FileText, Flame } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { exportUrl, getDebtWatch } from "@/lib/api";
import type { PropertyOpportunity } from "@/lib/types";
import { formatMoney, formatNumber, ownerHref } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeading } from "@/components/page-heading";
import { ScorePill } from "@/components/score-pill";

const THIS_YEAR = 2026;

function MaturityBadge({ year }: { year?: number }) {
  if (!year) return <span className="text-muted">—</span>;
  const yrs = year - THIS_YEAR;
  const tone = yrs <= 1 ? "red" : yrs <= 3 ? "amber" : "default";
  return <Badge tone={tone}>{year}</Badge>;
}

type SortKey =
  | "name"
  | "owner_name"
  | "units"
  | "loan_maturity_year"
  | "interest_rate"
  | "dscr"
  | "loan_amount"
  | "lender"
  | "debt_pressure"
  | "call_score";

const COLUMNS: Array<[SortKey, string]> = [
  ["name", "Property"],
  ["owner_name", "Owner"],
  ["units", "Units"],
  ["loan_maturity_year", "Maturity"],
  ["interest_rate", "Rate"],
  ["dscr", "Est. DSCR"],
  ["loan_amount", "Loan"],
  ["lender", "Lender"],
  ["debt_pressure", "Pressure"],
  ["call_score", "Call"]
];

export function DebtWatchPage() {
  const [rows, setRows] = useState<PropertyOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>("debt_pressure");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    getDebtWatch(200).then((data) => {
      setRows(data);
      setLoading(false);
    });
  }, []);

  const sorted = useMemo(() => {
    const missing = (v: unknown) => v === 0 || v === "" || v === null || v === undefined;
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      // N/A (0 / blank) always sorts to the bottom, regardless of direction —
      // so "lowest DSCR" shows the lowest real values first, dashes last.
      const am = missing(av);
      const bm = missing(bv);
      if (am && bm) return 0;
      if (am) return 1;
      if (bm) return -1;
      if (typeof av === "number" && typeof bv === "number") {
        return sortAsc ? av - bv : bv - av;
      }
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [rows, sortKey, sortAsc]);

  function sortBy(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  const imminent = rows.filter((r) => r.loan_maturity_year && r.loan_maturity_year - THIS_YEAR <= 2).length;
  const distressed = rows.filter((r) => r.dscr && r.dscr < 1.2).length;

  return (
    <div>
      <PageHeading eyebrow="Maturing Debt" title="Expiring Debt — Refi Pain">
        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-2 text-sm text-muted sm:flex">
            <Flame size={16} className="text-red" />
            Ranked by debt pressure
          </span>
          <Button asChild variant="secondary">
            <a href={exportUrl("/api/export/maturing-debt.pdf")}>
              <FileText size={15} />
              Debt PDF
            </a>
          </Button>
        </div>
      </PageHeading>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <Stat label="Maturing-debt sites" value={rows.length} />
        <Stat label="Maturing ≤ 2 years" value={imminent} tone="text-red" />
        <Stat label="Thin DSCR (< 1.2x)" value={distressed} tone="text-amber" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Owners facing a refinance — no hold requirement, debt is the trigger</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {rows.length === 0 ? (
            <div className="p-6 text-sm text-muted">
              {loading ? "Loading…" : "No maturing-debt opportunities found in the current data/market."}
            </div>
          ) : (
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full min-w-[1240px] border-collapse text-left">
                <thead className="bg-panel2 text-xs uppercase text-muted">
                  <tr>
                    {COLUMNS.map(([key, label]) => (
                      <th key={key} className="px-3 py-2">
                        <button className="inline-flex items-center gap-1 hover:text-amber" onClick={() => sortBy(key)}>
                          {label}
                          <ArrowUpDown size={12} className={sortKey === key ? "text-amber" : ""} />
                        </button>
                      </th>
                    ))}
                    <th className="px-3 py-2">Why Now</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((row) => (
                    <tr key={row.id} className="border-b border-border hover:bg-panel2/70">
                      <td className="px-3 py-3">
                        <Link href={`/properties/${row.id}`} className="inline-flex items-center gap-2 font-medium text-ink hover:text-amber">
                          <Building2 size={14} />
                          {row.name}
                        </Link>
                      </td>
                      <td className="px-3 py-3 text-sm">
                        <Link href={ownerHref(row.owner_name)} className="text-ink hover:text-amber">
                          {row.owner_name}
                        </Link>
                      </td>
                      <td className="px-3 py-3 text-sm text-ink">{row.units}</td>
                      <td className="px-3 py-3"><MaturityBadge year={row.loan_maturity_year} /></td>
                      <td className="px-3 py-3 text-sm text-ink">{row.interest_rate ? `${row.interest_rate.toFixed(2)}%` : "—"}</td>
                      <td className={`px-3 py-3 text-sm font-medium ${row.dscr && row.dscr < 1.2 ? "text-red" : "text-ink"}`}>
                        {row.dscr ? row.dscr.toFixed(2) : "—"}
                      </td>
                      <td className="px-3 py-3 text-sm text-ink">{row.loan_amount ? formatMoney(row.loan_amount) : "—"}</td>
                      <td className="px-3 py-3 text-sm text-ink">{row.lender || "—"}</td>
                      <td className="px-3 py-3 text-sm font-semibold text-amber">{row.debt_pressure ?? 0}</td>
                      <td className="px-3 py-3"><ScorePill value={row.call_score} /></td>
                      <td className="max-w-md px-3 py-3 text-sm text-muted">{row.why_now}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value, tone = "text-ink" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${tone}`}>{formatNumber(value)}</div>
    </div>
  );
}
