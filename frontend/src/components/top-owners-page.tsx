"use client";

import Link from "next/link";
import { Brain, Building2, ExternalLink, PhoneCall, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { generateCallPrep, getSummary, getTodayCallList } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CallPrep, OwnerProfile, TodayCallList } from "@/lib/types";
import { formatMoney, formatNumber, ownerHref } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DemoBadge } from "@/components/demo-badge";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

function CallPrepPanel({ prep }: { prep: CallPrep }) {
  return (
    <Card className="border-amber/30 bg-[#11100c]">
      <CardHeader>
        <CardTitle>AI Call Prep</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div>
          <div className="text-xs uppercase text-muted">Why owner may sell</div>
          <p className="mt-1 text-ink">{prep.why_owner_may_sell}</p>
        </div>
        <div>
          <div className="text-xs uppercase text-muted">Opening line</div>
          <p className="mt-1 text-ink">{prep.opening_call_line}</p>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <div className="text-xs uppercase text-muted">Talking points</div>
            <ul className="mt-1 space-y-1 text-ink">
              {prep.talking_points.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="text-xs uppercase text-muted">Possible objections</div>
            <ul className="mt-1 space-y-1 text-ink">
              {prep.possible_objections.map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          </div>
        </div>
        <div>
          <div className="text-xs uppercase text-muted">721 exchange angle</div>
          <p className="mt-1 text-ink">{prep.exchange_721_angle}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function OwnerRow({
  owner,
  onPrep
}: {
  owner: OwnerProfile;
  onPrep: (owner: OwnerProfile) => void;
}) {
  return (
    <tr className="border-b border-border hover:bg-panel2/70">
      <td className="px-3 py-3 text-sm text-muted">{owner.rank}</td>
      <td className="px-3 py-3">
        <Link href={ownerHref(owner.owner)} className="group inline-flex items-center gap-2 font-medium text-ink">
          {owner.owner}
          <ExternalLink size={13} className="text-muted group-hover:text-amber" />
        </Link>
        <div className="mt-1 flex flex-wrap gap-2">
          <DemoBadge dataStatus={owner.data_status} />
          <Badge tone={owner.owner_state === "CA" || owner.owner_state === "NV" ? "cyan" : "default"}>
            {owner.owner_state || "Owner State Unknown"}
          </Badge>
          {owner.potential_721_candidate && <Badge tone="amber">POTENTIAL 721</Badge>}
          <RecommendationBadge value={owner.recommendation} />
        </div>
      </td>
      <td className="px-3 py-3 text-sm text-ink">{owner.properties_owned}</td>
      <td className="px-3 py-3 text-sm text-ink">{formatNumber(owner.units_owned)}</td>
      <td className="px-3 py-3 text-sm text-ink">{owner.average_hold_period.toFixed(1)}</td>
      <td className="px-3 py-3">
        <ScorePill value={owner.call_score} />
      </td>
      <td className="max-w-sm px-3 py-3 text-sm text-ink">{owner.why_now}</td>
      <td className="max-w-sm px-3 py-3 text-sm text-muted">{owner.recommended_angle}</td>
      <td className="px-3 py-3">
        <Button variant="secondary" size="sm" onClick={() => onPrep(owner)}>
          <Brain size={14} />
          Prep
        </Button>
      </td>
    </tr>
  );
}

type Scope = "live" | "all";

export function TopOwnersPage() {
  const [data, setData] = useState<TodayCallList | null>(null);
  const [activePrep, setActivePrep] = useState<CallPrep | null>(null);
  const [prepOwner, setPrepOwner] = useState("");
  const [scope, setScope] = useState<Scope | null>(null);
  const [liveCount, setLiveCount] = useState(0);
  const [fallbackCount, setFallbackCount] = useState(0);

  // Decide the initial scope from provenance: show live imported data once any
  // exists (hiding demo), otherwise show everything (demo fallback) so the
  // dashboard is never empty.
  useEffect(() => {
    getSummary().then((summary) => {
      const live = summary.data_provenance.live_records ?? 0;
      setLiveCount(live);
      setFallbackCount(summary.data_provenance.fallback_records ?? 0);
      setScope(live > 0 ? "live" : "all");
    });
  }, []);

  useEffect(() => {
    if (!scope) return;
    getTodayCallList(scope).then(setData);
  }, [scope]);

  async function prep(owner: OwnerProfile) {
    setPrepOwner(owner.owner);
    setActivePrep({
      source: "loading",
      why_owner_may_sell: "Generating call prep...",
      opening_call_line: "",
      talking_points: [],
      possible_objections: [],
      exchange_721_angle: ""
    });
    const result = await generateCallPrep(owner.owner);
    setActivePrep(result);
  }

  const callList = data?.top_25_owners ?? [];
  const top10 = data?.top_10_owners ?? [];
  const newOpps = data?.top_new_opportunities ?? [];

  return (
    <div>
      <PageHeading eyebrow="Today's Call List" title="Top Owners To Call">
        <div className="flex flex-col items-end gap-2">
          {fallbackCount > 0 && (
            <div className="inline-flex overflow-hidden rounded-md border border-border">
              <button
                type="button"
                onClick={() => setScope("live")}
                disabled={liveCount === 0}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40",
                  scope === "live" ? "bg-green/15 text-green" : "bg-panel2 text-muted hover:text-ink"
                )}
                title={liveCount === 0 ? "No live imported records yet — import a file in Import & Review" : undefined}
              >
                <ShieldCheck size={13} />
                Live Data Only{liveCount > 0 ? ` (${liveCount})` : ""}
              </button>
              <button
                type="button"
                onClick={() => setScope("all")}
                className={cn(
                  "inline-flex items-center gap-1.5 border-l border-border px-3 py-1.5 text-xs font-medium transition-colors",
                  scope === "all" ? "bg-amber/15 text-amber" : "bg-panel2 text-muted hover:text-ink"
                )}
              >
                Include Demo Fallback
              </button>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-muted">
            <PhoneCall size={16} className="text-amber" />
            Sorted by Call Score
          </div>
        </div>
      </PageHeading>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Top 10 Owners</CardTitle>
            <Badge tone="green">Highest conviction</Badge>
          </CardHeader>
          <CardContent className="grid gap-3">
            {top10.map((owner) => (
              <Link
                href={ownerHref(owner.owner)}
                key={owner.owner}
                className="grid gap-3 rounded-md border border-border bg-panel2 p-3 transition-colors hover:border-amber/50 md:grid-cols-[1fr_auto]"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-ink">
                      #{owner.rank} {owner.owner}
                    </span>
                    <DemoBadge dataStatus={owner.data_status} />
                    <RecommendationBadge value={owner.recommendation} />
                    {owner.potential_721_candidate && <Badge tone="amber">721</Badge>}
                  </div>
                  <p className="mt-2 text-sm text-muted">{owner.why_now}</p>
                </div>
                <div className="flex items-center gap-2">
                  <ScorePill value={owner.call_score} />
                  <div className="text-right text-xs text-muted">
                    <div>{formatNumber(owner.units_owned)} units</div>
                    <div>{owner.average_hold_period.toFixed(0)} yrs held</div>
                  </div>
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Top New Opportunities</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {newOpps.map((property) => (
                <Link
                  href={`/properties/${property.id}`}
                  key={property.id}
                  className="block rounded-md border border-border bg-panel2 p-3 hover:border-amber/50"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-ink">
                        <Building2 size={15} className="text-amber" />
                        {property.name}
                        <DemoBadge dataStatus={property.data_status} />
                      </div>
                      <div className="mt-1 text-xs text-muted">{property.owner_name}</div>
                    </div>
                    <ScorePill value={property.call_score} />
                  </div>
                  <p className="mt-2 text-sm text-muted">{property.why_now}</p>
                </Link>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Acquisition Outcomes</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-md border border-border bg-panel2 p-3">
                <div className="text-xs uppercase text-muted">721 exposure</div>
                <div className="mt-1 text-lg font-semibold text-amber">
                  {formatMoney(top10.reduce((sum, row) => sum + row.estimated_tax_deferral, 0))}
                </div>
              </div>
              <div className="rounded-md border border-border bg-panel2 p-3">
                <div className="text-xs uppercase text-muted">Call-owner leads</div>
                <div className="mt-1 text-lg font-semibold text-green">
                  {callList.filter((row) => row.recommendation === "Call Owner").length}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {activePrep && (
        <div className="mt-4">
          <div className="mb-2 text-sm text-muted">Call prep for {prepOwner}</div>
          <CallPrepPanel prep={activePrep} />
        </div>
      )}

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Top 25 Owners</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full min-w-[1180px] border-collapse text-left">
            <thead className="bg-panel2 text-xs uppercase text-muted">
              <tr>
                <th className="px-3 py-2">Rank</th>
                <th className="px-3 py-2">Owner</th>
                <th className="px-3 py-2">Properties Owned</th>
                <th className="px-3 py-2">Units Owned</th>
                <th className="px-3 py-2">Years Held</th>
                <th className="px-3 py-2">Call Score</th>
                <th className="px-3 py-2">Why Now</th>
                <th className="px-3 py-2">Recommended Angle</th>
                <th className="px-3 py-2">Prep</th>
              </tr>
            </thead>
            <tbody>
              {callList.map((owner) => (
                <OwnerRow key={owner.owner} owner={owner} onPrep={prep} />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
