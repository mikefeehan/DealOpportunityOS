"use client";

import Link from "next/link";
import { MailSearch, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { enrichEmails, getOwners } from "@/lib/api";
import type { OwnerProfile } from "@/lib/types";
import { formatMoney, formatNumber, ownerHref } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { DemoBadge } from "@/components/demo-badge";
import { Input } from "@/components/ui/input";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

export function OwnerIntelligencePage() {
  const [owners, setOwners] = useState<OwnerProfile[]>([]);
  const [query, setQuery] = useState("");
  const [intrustMode, setIntrustMode] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState("");

  useEffect(() => {
    getOwners(intrustMode, 200).then(setOwners);
  }, [intrustMode]);

  async function runEnrich() {
    setEnriching(true);
    setEnrichMsg("");
    const result = await enrichEmails(25);
    setEnrichMsg(
      result.status === "ok"
        ? `Found ${result.emails_applied ?? 0} emails (${result.remaining_domains ?? 0} domains left)`
        : result.error || "Enrichment failed"
    );
    getOwners(intrustMode, 200).then(setOwners);
    setEnriching(false);
  }

  const filtered = useMemo(() => {
    const needle = query.toLowerCase();
    if (!needle) return owners;
    return owners.filter(
      (owner) =>
        owner.owner.toLowerCase().includes(needle) ||
        owner.mailing_address.toLowerCase().includes(needle) ||
        owner.owner_state.toLowerCase().includes(needle)
    );
  }, [owners, query]);

  return (
    <div>
      <PageHeading eyebrow="Owner Intelligence" title="Ranked Tucson Owners">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter owners" className="w-64 pl-9" />
          </div>
          <Button variant={intrustMode ? "default" : "secondary"} onClick={() => setIntrustMode(!intrustMode)}>
            InTrust Mode {intrustMode ? "On" : "Off"}
          </Button>
          <Button variant="secondary" onClick={runEnrich} disabled={enriching} title="Find owner emails via Hunter.io from owner websites">
            <MailSearch size={15} className={enriching ? "animate-pulse" : ""} />
            {enriching ? "Enriching" : "Enrich emails"}
          </Button>
          {enrichMsg && <span className="text-xs text-muted">{enrichMsg}</span>}
        </div>
      </PageHeading>
      <Card>
        <CardHeader>
          <CardTitle>Owner Profiles</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full min-w-[1100px] border-collapse text-left">
            <thead className="bg-panel2 text-xs uppercase text-muted">
              <tr>
                <th className="px-3 py-2">Rank</th>
                <th className="px-3 py-2">Owner</th>
                <th className="px-3 py-2">Portfolio</th>
                <th className="px-3 py-2">Avg Hold</th>
                <th className="px-3 py-2">Call</th>
                <th className="px-3 py-2">Fit</th>
                <th className="px-3 py-2">Motivation</th>
                <th className="px-3 py-2">721</th>
                <th className="px-3 py-2">Why Now</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((owner) => (
                <tr key={owner.owner} className="border-b border-border hover:bg-panel2/70">
                  <td className="px-3 py-3 text-sm text-muted">{owner.rank}</td>
                  <td className="px-3 py-3">
                    <Link href={ownerHref(owner.owner)} className="font-medium text-ink hover:text-amber">
                      {owner.owner}
                    </Link>
                    <div className="mt-1 flex flex-wrap gap-2">
                      <DemoBadge dataStatus={owner.data_status} />
                      <Badge>{owner.owner_state}</Badge>
                      <RecommendationBadge value={owner.recommendation} />
                    </div>
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">
                    {owner.properties_owned} props / {formatNumber(owner.units_owned)} units
                    <div className="mt-1 text-xs text-muted">{formatMoney(owner.estimated_portfolio_value)}</div>
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">{owner.average_hold_period.toFixed(1)} yrs</td>
                  <td className="px-3 py-3">
                    <ScorePill value={owner.call_score} />
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">{owner.fit_score.toFixed(1)}</td>
                  <td className="px-3 py-3 text-sm text-ink">{owner.motivation_score.toFixed(1)}</td>
                  <td className="px-3 py-3 text-sm text-ink">
                    {owner.potential_721_candidate ? <Badge tone="amber">Potential</Badge> : <Badge>Not primary</Badge>}
                  </td>
                  <td className="max-w-md px-3 py-3 text-sm text-muted">{owner.why_now}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
