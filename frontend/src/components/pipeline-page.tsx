"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getPipeline, updatePipeline } from "@/lib/api";
import type { PipelinePayload, PropertyOpportunity } from "@/lib/types";
import { ownerHref } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { PageHeading } from "@/components/page-heading";
import { RecommendationBadge } from "@/components/recommendation-badge";
import { ScorePill } from "@/components/score-pill";

export function PipelinePage() {
  const [payload, setPayload] = useState<PipelinePayload | null>(null);

  async function refresh() {
    setPayload(await getPipeline());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function move(property: PropertyOpportunity, stage: string) {
    await updatePipeline(property.id, { stage, notes: property.notes || "" });
    refresh();
  }

  const stages = payload?.stages ?? [];
  const grouped = payload?.properties_by_stage ?? {};

  return (
    <div>
      <PageHeading eyebrow="Pipeline" title="Acquisition Outcomes Board" />
      <div className="grid gap-3 overflow-x-auto pb-2 scrollbar-thin xl:grid-cols-7">
        {stages.map((stage) => {
          const rows = grouped[stage] ?? [];
          return (
            <Card key={stage} className="min-w-72 xl:min-w-0">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>{stage}</CardTitle>
                <span className="rounded-md border border-border bg-panel2 px-2 py-0.5 text-xs text-muted">{rows.length}</span>
              </CardHeader>
              <CardContent className="space-y-3">
                {rows.map((property) => (
                  <div key={property.id} className="rounded-md border border-border bg-panel2 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link href={`/properties/${property.id}`} className="font-medium text-ink hover:text-amber">
                          {property.name}
                        </Link>
                        <Link href={ownerHref(property.owner_name)} className="mt-1 block text-xs text-muted hover:text-amber">
                          {property.owner_name}
                        </Link>
                      </div>
                      <ScorePill value={property.call_score} className="min-w-14 text-xs" />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <RecommendationBadge value={property.recommendation} />
                    </div>
                    <p className="mt-3 text-xs text-muted">{property.why_now}</p>
                    <Select value={stage} onChange={(event) => move(property, event.target.value)} className="mt-3 w-full">
                      {stages.map((item) => (
                        <option key={item} value={item}>
                          Move to {item}
                        </option>
                      ))}
                    </Select>
                  </div>
                ))}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
