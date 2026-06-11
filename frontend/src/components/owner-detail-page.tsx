"use client";

import Link from "next/link";
import { Brain, Building2, MapPin } from "lucide-react";
import { useEffect, useState } from "react";
import { generateCallPrep, getOwner } from "@/lib/api";
import type { CallPrep, OwnerProfile } from "@/lib/types";
import { formatMoney, formatNumber } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DemoBadge } from "@/components/demo-badge";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

export function OwnerDetailPage({ ownerName }: { ownerName: string }) {
  const [owner, setOwner] = useState<OwnerProfile | null>(null);
  const [prep, setPrep] = useState<CallPrep | null>(null);

  useEffect(() => {
    getOwner(ownerName).then(setOwner);
  }, [ownerName]);

  async function onPrep() {
    if (!owner) return;
    setPrep({
      source: "loading",
      why_owner_may_sell: "Generating call prep...",
      opening_call_line: "",
      talking_points: [],
      possible_objections: [],
      exchange_721_angle: ""
    });
    setPrep(await generateCallPrep(owner.owner));
  }

  if (!owner) {
    return <PageHeading eyebrow="Owner Intelligence" title="Loading owner profile" />;
  }

  return (
    <div>
      <PageHeading eyebrow="Owner Intelligence" title={owner.owner}>
        <div className="flex items-center gap-2">
          <DemoBadge dataStatus={owner.data_status} />
          <Button onClick={onPrep}>
            <Brain size={15} />
            Generate AI Call Prep
          </Button>
        </div>
      </PageHeading>

      {owner.data_status === "seeded_fallback" && (
        <div className="mb-4 rounded-md border border-red/35 bg-red/10 px-3 py-2 text-sm text-red">
          This is seeded demo data — not a verified real owner. Do not contact. Import and confirm a real
          record on the Import &amp; Review page to replace it.
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
        <Card>
          <CardHeader>
            <CardTitle>Owner Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-xs uppercase text-muted">Mailing address</div>
              <div className="mt-1 flex items-start gap-2 text-sm text-ink">
                <MapPin size={15} className="mt-0.5 text-amber" />
                {owner.mailing_address}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Properties" value={owner.properties_owned} />
              <Metric label="Units" value={formatNumber(owner.units_owned)} />
              <Metric label="Avg Hold" value={`${owner.average_hold_period.toFixed(1)} yrs`} />
              <Metric label="Portfolio Value" value={formatMoney(owner.estimated_portfolio_value)} />
              <Metric label="Oldest Buy" value={owner.oldest_acquisition} />
              <Metric label="Newest Buy" value={owner.newest_acquisition} />
            </div>
            <div className="flex flex-wrap gap-2">
              <RecommendationBadge value={owner.recommendation} />
              {owner.potential_721_candidate && <Badge tone="amber">POTENTIAL 721 CANDIDATE</Badge>}
              <Badge tone="cyan">{owner.owner_state} OWNER</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Why Call Now</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <ScoreBlock label="Call Score" value={owner.call_score} />
              <ScoreBlock label="Fit Score" value={owner.fit_score} />
              <ScoreBlock label="Motivation" value={owner.motivation_score} />
            </div>
            <div className="rounded-md border border-border bg-panel2 p-3">
              <div className="text-xs uppercase text-muted">Why Now</div>
              <p className="mt-2 text-sm text-ink">{owner.why_now}</p>
            </div>
            <div className="rounded-md border border-border bg-panel2 p-3">
              <div className="text-xs uppercase text-muted">Recommended Outreach Angle</div>
              <p className="mt-2 text-sm text-ink">{owner.recommended_angle}</p>
            </div>
            <div className="rounded-md border border-border bg-panel2 p-3">
              <div className="text-xs uppercase text-muted">Estimated tax deferral opportunity</div>
              <p className="mt-2 text-lg font-semibold text-amber">{formatMoney(owner.estimated_tax_deferral)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {prep && (
        <Card className="mt-4 border-amber/30 bg-[#11100c]">
          <CardHeader>
            <CardTitle>AI Call Prep</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm">
            <p className="text-ink">{prep.why_owner_may_sell}</p>
            <div className="rounded-md border border-border bg-panel2 p-3 text-ink">{prep.opening_call_line}</div>
            <div className="grid gap-3 md:grid-cols-3">
              <ListBlock title="Talking Points" items={prep.talking_points} />
              <ListBlock title="Objections" items={prep.possible_objections} />
              <div className="rounded-md border border-border bg-panel2 p-3">
                <div className="text-xs uppercase text-muted">721 Angle</div>
                <p className="mt-2 text-ink">{prep.exchange_721_angle}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Property Details</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full min-w-[900px] border-collapse text-left">
            <thead className="bg-panel2 text-xs uppercase text-muted">
              <tr>
                <th className="px-3 py-2">Property</th>
                <th className="px-3 py-2">Units</th>
                <th className="px-3 py-2">Year</th>
                <th className="px-3 py-2">Hold</th>
                <th className="px-3 py-2">Call</th>
                <th className="px-3 py-2">Outcome</th>
                <th className="px-3 py-2">Why Now</th>
              </tr>
            </thead>
            <tbody>
              {owner.properties.map((property) => (
                <tr key={property.id} className="border-b border-border hover:bg-panel2/70">
                  <td className="px-3 py-3">
                    <Link href={`/properties/${property.id}`} className="inline-flex items-center gap-2 font-medium text-ink hover:text-amber">
                      <Building2 size={15} />
                      {property.name}
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-sm text-ink">{property.units}</td>
                  <td className="px-3 py-3 text-sm text-ink">{property.year_built}</td>
                  <td className="px-3 py-3 text-sm text-ink">{property.hold_period.toFixed(1)} yrs</td>
                  <td className="px-3 py-3">
                    <ScorePill value={property.call_score} />
                  </td>
                  <td className="px-3 py-3">
                    <RecommendationBadge value={property.recommendation} />
                  </td>
                  <td className="max-w-md px-3 py-3 text-sm text-muted">{property.why_now}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold text-ink">{value}</div>
    </div>
  );
}

function ScoreBlock({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-2">
        <ScorePill value={value} />
      </div>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{title}</div>
      <ul className="mt-2 space-y-1 text-ink">
        {items.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </div>
  );
}
