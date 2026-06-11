"use client";

import Link from "next/link";
import { Building2, Flame } from "lucide-react";
import { useEffect, useState } from "react";
import { getDebtWatch } from "@/lib/api";
import type { PropertyOpportunity } from "@/lib/types";
import { formatMoney, formatNumber, ownerHref } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
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

export function DebtWatchPage() {
  const [rows, setRows] = useState<PropertyOpportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDebtWatch(200).then((data) => {
      setRows(data);
      setLoading(false);
    });
  }, []);

  const imminent = rows.filter((r) => r.loan_maturity_year && r.loan_maturity_year - THIS_YEAR <= 2).length;
  const distressed = rows.filter((r) => r.dscr && r.dscr < 1.2).length;

  return (
    <div>
      <PageHeading eyebrow="Maturing Debt" title="Expiring Debt — Refi Pain">
        <div className="flex items-center gap-2 text-sm text-muted">
          <Flame size={16} className="text-red" />
          Ranked by debt pressure
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
              <table className="w-full min-w-[1080px] border-collapse text-left">
                <thead className="bg-panel2 text-xs uppercase text-muted">
                  <tr>
                    <th className="px-3 py-2">Property</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Units</th>
                    <th className="px-3 py-2">Maturity</th>
                    <th className="px-3 py-2">Rate</th>
                    <th className="px-3 py-2">Est. DSCR</th>
                    <th className="px-3 py-2">Loan</th>
                    <th className="px-3 py-2">Pressure</th>
                    <th className="px-3 py-2">Call</th>
                    <th className="px-3 py-2">Why Now</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
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
