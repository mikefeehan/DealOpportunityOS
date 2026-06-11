"use client";

import Link from "next/link";
import { ArrowUpDown, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getOpportunities } from "@/lib/api";
import type { PropertyOpportunity } from "@/lib/types";
import { formatMoney, ownerHref } from "@/lib/utils";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

type SortKey =
  | "name"
  | "owner_name"
  | "lender"
  | "units"
  | "year_built"
  | "hold_period"
  | "rent_gap"
  | "dscr"
  | "loan_maturity_year"
  | "call_score";

const COLUMNS: Array<[SortKey, string]> = [
  ["name", "Property"],
  ["owner_name", "Owner"],
  ["lender", "Lender"],
  ["units", "Units"],
  ["year_built", "Built"],
  ["hold_period", "Hold"],
  ["rent_gap", "Rent Gap"],
  ["dscr", "DSCR"],
  ["loan_maturity_year", "Maturity"],
  ["call_score", "Call"]
];

export function DealsPage() {
  const [rows, setRows] = useState<PropertyOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [minUnits, setMinUnits] = useState("");
  const [lender, setLender] = useState("");
  const [minGap, setMinGap] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("call_score");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    getOpportunities({ intrust_mode: false, data_scope: "live", limit: 500 }).then((data) => {
      setRows(data);
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(() => {
    const needle = query.toLowerCase();
    const lenderNeedle = lender.toLowerCase();
    const minU = Number(minUnits) || 0;
    const minG = Number(minGap) || 0;
    return rows.filter((r) => {
      if (needle && !`${r.name} ${r.owner_name} ${r.lender ?? ""} ${r.submarket} ${r.address}`.toLowerCase().includes(needle)) return false;
      if (lenderNeedle && !(r.lender ?? "").toLowerCase().includes(lenderNeedle)) return false;
      if (minU && r.units < minU) return false;
      if (minG && (r.rent_gap ?? 0) < minG) return false;
      if (recommendation && r.recommendation !== recommendation) return false;
      return true;
    });
  }, [rows, query, lender, minUnits, minGap, recommendation]);

  const sorted = useMemo(() => {
    const missing = (v: unknown) => v === 0 || v === "" || v === null || v === undefined;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const am = missing(av);
      const bm = missing(bv);
      if (am && bm) return 0;
      if (am) return 1;
      if (bm) return -1;
      if (typeof av === "number" && typeof bv === "number") return sortAsc ? av - bv : bv - av;
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [filtered, sortKey, sortAsc]);

  function sortBy(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  return (
    <div>
      <PageHeading eyebrow="Deal Finder" title="All Deals">
        <span className="text-sm text-muted">{filtered.length} of {rows.length}</span>
      </PageHeading>

      <Card>
        <CardHeader className="gap-3">
          <CardTitle>Search & filter every property</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search owner, property, submarket" className="w-60 pl-9" />
            </div>
            <Input value={lender} onChange={(e) => setLender(e.target.value)} placeholder="Lender" className="w-40" />
            <Input value={minUnits} onChange={(e) => setMinUnits(e.target.value)} type="number" placeholder="Min units" className="w-28" />
            <Input value={minGap} onChange={(e) => setMinGap(e.target.value)} type="number" placeholder="Min rent gap %" className="w-32" />
            <Select value={recommendation} onChange={(e) => setRecommendation(e.target.value)}>
              <option value="">All outcomes</option>
              <option value="Call Owner">Call Owner</option>
              <option value="Monitor">Monitor</option>
              <option value="Ignore">Ignore</option>
            </Select>
          </div>
        </CardHeader>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full min-w-[1200px] border-collapse text-left">
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
                <th className="px-3 py-2">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr key={row.id} className="border-b border-border hover:bg-panel2/70">
                  <td className="px-3 py-3">
                    <Link href={`/properties/${row.id}`} className="font-medium text-ink hover:text-amber">{row.name}</Link>
                    <div className="mt-0.5 text-xs text-muted">{row.submarket}</div>
                  </td>
                  <td className="px-3 py-3 text-sm"><Link href={ownerHref(row.owner_name)} className="text-ink hover:text-amber">{row.owner_name}</Link></td>
                  <td className="px-3 py-3 text-sm text-ink">{row.lender || "—"}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.units}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.year_built || "—"}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.hold_period.toFixed(0)}y</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.rent_gap ? `${row.rent_gap.toFixed(0)}%` : "—"}</td>
                  <td className={`px-3 py-3 text-sm ${row.dscr && row.dscr < 1.2 ? "text-red font-medium" : "text-ink"}`}>{row.dscr ? row.dscr.toFixed(2) : "—"}</td>
                  <td className="px-3 py-3 text-sm text-ink">{row.loan_maturity_year || "—"}</td>
                  <td className="px-3 py-3"><ScorePill value={row.call_score} /></td>
                  <td className="px-3 py-3"><RecommendationBadge value={row.recommendation} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && sorted.length === 0 && <div className="p-6 text-sm text-muted">No deals match these filters.</div>}
        </div>
      </Card>
    </div>
  );
}
