"use client";

import Link from "next/link";
import { Building2, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { getProperty, updatePipeline } from "@/lib/api";
import type { PropertyOpportunity } from "@/lib/types";
import { formatMoney, formatNumber, ownerHref } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

const stages = ["Identified", "Research", "Contacted", "Meeting", "LOI", "Dead", "Closed"];

export function PropertyDetailPage({ id }: { id: string }) {
  const [property, setProperty] = useState<PropertyOpportunity | null>(null);
  const [stage, setStage] = useState("Identified");
  const [notes, setNotes] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getProperty(id).then((result) => {
      setProperty(result);
      setStage(result.stage);
      setNotes(result.notes || "");
    });
  }, [id]);

  async function savePipeline() {
    if (!property) return;
    await updatePipeline(property.id, { stage, notes });
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  }

  if (!property) {
    return <PageHeading eyebrow="Property Detail" title="Loading property" />;
  }

  return (
    <div>
      <PageHeading eyebrow="Property Detail" title={property.name}>
        <RecommendationBadge value={property.recommendation} />
      </PageHeading>

      <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <CardTitle>Ownership</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-xs uppercase text-muted">Owner</div>
              <Link href={ownerHref(property.owner_name)} className="mt-1 inline-flex items-center gap-2 text-lg font-semibold text-ink hover:text-amber">
                {property.owner_name}
              </Link>
            </div>
            <div>
              <div className="text-xs uppercase text-muted">Mailing address</div>
              <div className="mt-1 text-sm text-ink">{property.mailing_address}</div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Parcel ID" value={property.parcel_id} />
              <Metric label="Owner State" value={property.owner_state || "Unknown"} />
              <Metric label="Held" value={`${property.hold_period.toFixed(1)} yrs`} />
              <Metric label="Last Sale" value={property.last_sale_year} />
            </div>
            <div className="flex flex-wrap gap-2">
              {property.potential_721_candidate && <Badge tone="amber">POTENTIAL 721 CANDIDATE</Badge>}
              <Badge tone="cyan">{property.source}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Acquisition Decision</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-3">
              <ScoreBlock label="Call Score" value={property.call_score} />
              <ScoreBlock label="Fit Score" value={property.fit_score} />
              <ScoreBlock label="Motivation" value={property.motivation_score} />
            </div>
            <div className="rounded-md border border-border bg-panel2 p-3">
              <div className="text-xs uppercase text-muted">Why Now</div>
              <p className="mt-2 text-sm text-ink">{property.why_now}</p>
            </div>
            <div className="rounded-md border border-border bg-panel2 p-3">
              <div className="text-xs uppercase text-muted">Recommended Outreach Angle</div>
              <p className="mt-2 text-sm text-ink">{property.recommended_angle}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Property Facts</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <Metric label="Units" value={formatNumber(property.units)} />
            <Metric label="Built" value={property.year_built} />
            <Metric label="Sq Ft" value={formatNumber(property.building_sqft)} />
            <Metric label="Submarket" value={property.submarket} />
            <Metric label="Assessed" value={formatMoney(property.assessed_value)} />
            <Metric label="Tax Deferral" value={formatMoney(property.estimated_tax_deferral)} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rent Analysis</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <Metric label="Current Rent" value={formatMoney(property.average_rent, false)} />
            <Metric label="Market Rent" value={formatMoney(property.market_rent, false)} />
            <Metric label="Rent Gap" value={`${property.rent_gap.toFixed(1)}%`} />
            <Metric label="Basis Gap" value={`${property.basis_gap.toFixed(1)}%`} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Select value={stage} onChange={(event) => setStage(event.target.value)}>
              {stages.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
            <Textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Acquisition notes, call result, broker intel, ownership clues..." />
            <Button onClick={savePipeline}>
              <Save size={15} />
              {saved ? "Saved" : "Save Notes"}
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader className="flex flex-row items-center gap-2">
          <Building2 size={16} className="text-amber" />
          <CardTitle>Score Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {property.score_breakdown.map((item) => (
            <div key={item.factor} className="rounded-md border border-border bg-panel2 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-medium text-ink">{item.factor}</div>
                <Badge>{item.weight}%</Badge>
              </div>
              <div className="mt-2 flex items-end justify-between">
                <ScorePill value={item.score} />
                <div className="text-xs text-muted">{item.raw}</div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-ink">{value}</div>
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
