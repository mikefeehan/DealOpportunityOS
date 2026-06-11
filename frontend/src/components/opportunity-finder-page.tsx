"use client";

import Link from "next/link";
import { ArrowUpDown, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getOpportunities } from "@/lib/api";
import type { PropertyOpportunity } from "@/lib/types";
import { formatMoney, ownerHref } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { DemoBadge } from "@/components/demo-badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

type SortKey =
  | "call_score"
  | "fit_score"
  | "motivation_score"
  | "name"
  | "units"
  | "year_built"
  | "owner_name"
  | "hold_period"
  | "owner_state"
  | "rent_gap"
  | "assessed_value";

export function OpportunityFinderPage() {
  const [rows, setRows] = useState<PropertyOpportunity[]>([]);
  const [query, setQuery] = useState("");
  const [intrustMode, setIntrustMode] = useState(true);
  const [recommendation, setRecommendation] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("call_score");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    getOpportunities({ intrust_mode: intrustMode, q: query, recommendation, limit: 200 }).then(setRows);
  }, [intrustMode, query, recommendation]);

  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") {
        return sortAsc ? av - bv : bv - av;
      }
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [rows, sortAsc, sortKey]);

  function sortBy(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  const headers: Array<[SortKey, string]> = [
    ["call_score", "Call Score"],
    ["fit_score", "Fit"],
    ["motivation_score", "Motivation"],
    ["name", "Property"],
    ["units", "Units"],
    ["year_built", "Year Built"],
    ["owner_name", "Owner"],
    ["hold_period", "Hold Period"],
    ["owner_state", "Owner State"],
    ["rent_gap", "Rent Gap"],
    ["assessed_value", "Assessed Value"]
  ];

  return (
    <div>
      <PageHeading eyebrow="Opportunity Finder" title="Top 25 Properties And Beyond" />

      <Card>
        <CardHeader className="gap-3 md:flex-row md:items-center md:justify-between">
          <CardTitle>Ranked by owner call priority</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter owner, asset, parcel" className="w-64 pl-9" />
            </div>
            <Select value={recommendation} onChange={(event) => setRecommendation(event.target.value)}>
              <option value="">All outcomes</option>
              <option value="Call Owner">Call Owner</option>
              <option value="Monitor">Monitor</option>
              <option value="Ignore">Ignore</option>
            </Select>
            <Button variant={intrustMode ? "default" : "secondary"} onClick={() => setIntrustMode(!intrustMode)}>
              InTrust Mode {intrustMode ? "On" : "Off"}
            </Button>
          </div>
        </CardHeader>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full min-w-[1320px] border-collapse text-left">
            <thead className="bg-panel2 text-xs uppercase text-muted">
              <tr>
                {headers.map(([key, label]) => (
                  <th key={key} className="px-3 py-2">
                    <button className="inline-flex items-center gap-1 hover:text-amber" onClick={() => sortBy(key)}>
                      {label}
                      <ArrowUpDown size={13} />
                    </button>
                  </th>
                ))}
                <th className="px-3 py-2">Outcome</th>
                <th className="px-3 py-2">Why Now</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr key={row.id} className="border-b border-border hover:bg-panel2/70">
                  <td className="px-3 py-3">
                    <ScorePill value={row.call_score} />
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">{row.fit_score.toFixed(1)}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.motivation_score.toFixed(1)}</td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link href={`/properties/${row.id}`} className="font-medium text-ink hover:text-amber">
                        {row.name}
                      </Link>
                      <DemoBadge dataStatus={row.data_status} />
                    </div>
                    <div className="mt-1 text-xs text-muted">{row.parcel_id}</div>
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">{row.units}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.year_built}</td>
                  <td className="px-3 py-3">
                    <Link href={ownerHref(row.owner_name)} className="text-sm text-ink hover:text-amber">
                      {row.owner_name}
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">{row.hold_period.toFixed(1)} yrs</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.owner_state}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.rent_gap.toFixed(1)}%</td>
                  <td className="px-3 py-3 text-sm text-ink">{formatMoney(row.assessed_value)}</td>
                  <td className="px-3 py-3">
                    <RecommendationBadge value={row.recommendation} />
                  </td>
                  <td className="max-w-md px-3 py-3 text-sm text-muted">{row.why_now}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
