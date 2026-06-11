"use client";

import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, Building2, CheckCircle2, Handshake, LineChart, Phone, Target, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { getMarketContext, getOwners, getOpportunities, getSummary } from "@/lib/api";
import type { MarketContext, MarketSummary, OwnerProfile, PropertyOpportunity } from "@/lib/types";
import { formatMoney, formatNumber, ownerHref } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeading } from "@/components/page-heading";
import { ScorePill } from "@/components/score-pill";

function ContextMetric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-md border border-border bg-panel2 p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold text-ink">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}

function pct(value?: number | null) {
  if (value === null || value === undefined) return "—";
  return `${value > 0 ? "+" : ""}${value}%`;
}

function MarketContextPanel({ ctx }: { ctx: MarketContext }) {
  if (!ctx.available) return null;
  const { rent, supply, demographics } = ctx;
  return (
    <Card className="mt-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <LineChart size={16} className="text-amber" />
          Tucson Market Context
        </CardTitle>
        <Badge tone="cyan">HelloData{ctx.as_of ? ` · ${ctx.as_of}` : ""}</Badge>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <ContextMetric
          label="Avg Effective Rent"
          value={rent.avg_effective ? formatMoney(rent.avg_effective, false) : "—"}
          sub={rent.avg_asking ? `${formatMoney(rent.avg_asking, false)} asking · ${pct(rent.concession_pct ? -rent.concession_pct : null)} concession` : undefined}
        />
        <ContextMetric label="Rent Growth (YoY)" value={pct(rent.growth_yoy)} sub="market median" />
        <ContextMetric
          label="Supply Pipeline"
          value={supply.pipeline_total_units ? `${formatNumber(supply.pipeline_total_units)} units` : "—"}
          sub={supply.under_construction_units ? `${formatNumber(supply.under_construction_units)} under construction` : undefined}
        />
        <ContextMetric
          label="Market Size"
          value={supply.existing_units ? `${formatNumber(supply.existing_units)} units` : "—"}
          sub={supply.existing_properties ? `${formatNumber(supply.existing_properties)} properties` : undefined}
        />
        <ContextMetric label="Population" value={demographics.population ? formatNumber(demographics.population) : "—"} />
        <ContextMetric label="Median Income" value={demographics.median_income ? formatMoney(demographics.median_income, false) : "—"} />
        <ContextMetric label="Employment Rate" value={demographics.employment_rate ? `${demographics.employment_rate}%` : "—"} />
        <ContextMetric
          label="HelloData Rent Comps"
          value={ctx.comp_set.properties ? `${formatNumber(ctx.comp_set.properties)} comps` : "—"}
          sub={ctx.comp_set.median_rent ? `${formatMoney(ctx.comp_set.median_rent, false)} median rent` : undefined}
        />
      </CardContent>
    </Card>
  );
}

const statIcons = [Building2, Target, Users, BriefcaseBusiness, Phone];

function StatCard({ label, value, index }: { label: string; value: string | number; index: number }) {
  const Icon = statIcons[index % statIcons.length];
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <div className="text-xs uppercase text-muted">{label}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{value}</div>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-md border border-amber/30 bg-amber/10 text-amber">
          <Icon size={18} />
        </div>
      </CardContent>
    </Card>
  );
}

export function CommandCenterPage() {
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [owners, setOwners] = useState<OwnerProfile[]>([]);
  const [properties, setProperties] = useState<PropertyOpportunity[]>([]);
  const [context, setContext] = useState<MarketContext | null>(null);

  useEffect(() => {
    getSummary().then(setSummary);
    getMarketContext().then(setContext);
    getOwners(true, 8).then(setOwners);
    getOpportunities({ intrust_mode: true, limit: 8 }).then(setProperties);
  }, []);

  const reporting = summary?.reporting;

  return (
    <div>
      <PageHeading eyebrow="Market Command Center" title="Tucson Acquisition Pulse" />
      {context && <MarketContextPanel ctx={context} />}
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total Properties" value={summary?.total_properties ?? 0} index={0} />
        <StatCard label="High Score Targets" value={summary?.high_score_targets ?? 0} index={1} />
        <StatCard label="Long Hold Owners" value={summary?.long_hold_owners ?? 0} index={2} />
        <StatCard label="Avg Hold Period" value={`${summary?.average_hold_period ?? 0} yrs`} index={3} />
        <StatCard label="Avg Rent Gap" value={`${summary?.average_rent_gap ?? 0}%`} index={4} />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Acquisition Outcome Reporting</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {[
              ["Owners researched", reporting?.owners_researched ?? 0, Users],
              ["Owners contacted", reporting?.owners_contacted ?? 0, Phone],
              ["Meetings generated", reporting?.meetings_generated ?? 0, Handshake],
              ["Off-market opps", reporting?.off_market_opportunities ?? 0, Target],
              ["LOIs submitted", reporting?.lois_submitted ?? 0, BriefcaseBusiness],
              ["Deals closed", reporting?.deals_closed ?? 0, CheckCircle2]
            ].map(([label, value, Icon]) => {
              const MetricIcon = Icon as typeof Users;
              return (
                <div key={label as string} className="rounded-md border border-border bg-panel2 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase text-muted">{label as string}</span>
                    <MetricIcon size={15} className="text-amber" />
                  </div>
                  <div className="mt-2 text-xl font-semibold text-ink">{value as number}</div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>InTrust Mode Filters</CardTitle>
            <Badge tone="amber">Default Call Sheet</Badge>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm text-muted md:grid-cols-2">
            <div>75+ units</div>
            <div>Built 1970-2015</div>
            <div>Held more than 10 years</div>
            <div>Private / family / trust ownership</div>
            <div>Non-institutional ownership</div>
            <div>Owner location not required</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Owners Most Likely To Transact</CardTitle>
            <Link href="/" className="inline-flex items-center gap-1 text-sm text-amber">
              Full call list <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {owners.map((owner) => (
              <Link key={owner.owner} href={ownerHref(owner.owner)} className="flex items-center justify-between gap-3 rounded-md border border-border bg-panel2 p-3 hover:border-amber/50">
                <div>
                  <div className="font-medium text-ink">{owner.owner}</div>
                  <div className="mt-1 text-sm text-muted">
                    {formatNumber(owner.units_owned)} units. {owner.why_now}
                  </div>
                </div>
                <ScorePill value={owner.call_score} />
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Assets That Fit Buy Box</CardTitle>
            <Link href="/opportunities" className="inline-flex items-center gap-1 text-sm text-amber">
              Finder <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {properties.map((property) => (
              <Link key={property.id} href={`/properties/${property.id}`} className="flex items-center justify-between gap-3 rounded-md border border-border bg-panel2 p-3 hover:border-amber/50">
                <div>
                  <div className="font-medium text-ink">{property.name}</div>
                  <div className="mt-1 text-sm text-muted">
                    {property.units} units. {property.why_now}
                  </div>
                </div>
                <ScorePill value={property.call_score} />
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
