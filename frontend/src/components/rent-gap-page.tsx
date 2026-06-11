"use client";

import Link from "next/link";
import { Building2, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getOpportunities } from "@/lib/api";
import type { PropertyOpportunity } from "@/lib/types";
import { formatMoney, ownerHref } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeading } from "@/components/page-heading";
import { ScorePill } from "@/components/score-pill";

export function RentGapPage() {
  const [rows, setRows] = useState<PropertyOpportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOpportunities({ intrust_mode: false, data_scope: "live", limit: 500 }).then((data) => {
      setRows(data);
      setLoading(false);
    });
  }, []);

  const candidates = useMemo(
    () => rows.filter((r) => (r.rent_gap ?? 0) > 0).sort((a, b) => (b.rent_gap ?? 0) - (a.rent_gap ?? 0)),
    [rows]
  );
  const avgGap = candidates.length
    ? candidates.reduce((s, r) => s + (r.rent_gap ?? 0), 0) / candidates.length
    : 0;

  return (
    <div>
      <PageHeading eyebrow="Value-Add" title="Top Rent-Gap Candidates">
        <div className="flex items-center gap-2 text-sm text-muted">
          <TrendingUp size={16} className="text-green" />
          In-place vs. net-effective market rent
        </div>
      </PageHeading>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <Stat label="Candidates with upside" value={`${candidates.length}`} />
        <Stat label="Avg rent gap" value={`${avgGap.toFixed(0)}%`} />
        <Stat label="Biggest gap" value={candidates[0] ? `${candidates[0].rent_gap.toFixed(0)}%` : "—"} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ranked by mark-to-market rent upside (affordable / unrealizable excluded)</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {candidates.length === 0 ? (
            <div className="p-6 text-sm text-muted">{loading ? "Loading…" : "No rent-gap candidates in the current data."}</div>
          ) : (
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full min-w-[1000px] border-collapse text-left">
                <thead className="bg-panel2 text-xs uppercase text-muted">
                  <tr>
                    <th className="px-3 py-2">Property</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Units</th>
                    <th className="px-3 py-2">In-Place</th>
                    <th className="px-3 py-2">Market (NER)</th>
                    <th className="px-3 py-2">Rent Gap</th>
                    <th className="px-3 py-2">Monthly Upside</th>
                    <th className="px-3 py-2">Call</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((row) => {
                    const upside = Math.max(0, (row.market_rent - row.average_rent) * row.units);
                    return (
                      <tr key={row.id} className="border-b border-border hover:bg-panel2/70">
                        <td className="px-3 py-3">
                          <Link href={`/properties/${row.id}`} className="inline-flex items-center gap-2 font-medium text-ink hover:text-amber">
                            <Building2 size={14} />
                            {row.name}
                          </Link>
                          <div className="mt-0.5 text-xs text-muted">{row.submarket}</div>
                        </td>
                        <td className="px-3 py-3 text-sm"><Link href={ownerHref(row.owner_name)} className="text-ink hover:text-amber">{row.owner_name}</Link></td>
                        <td className="px-3 py-3 text-sm text-ink">{row.units}</td>
                        <td className="px-3 py-3 text-sm text-ink">{formatMoney(row.average_rent, false)}</td>
                        <td className="px-3 py-3 text-sm text-ink">{formatMoney(row.market_rent, false)}</td>
                        <td className="px-3 py-3 text-sm font-semibold text-green">{row.rent_gap.toFixed(0)}%</td>
                        <td className="px-3 py-3 text-sm text-ink">{formatMoney(upside)}</td>
                        <td className="px-3 py-3"><ScorePill value={row.call_score} /></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-ink">{value}</div>
    </div>
  );
}
