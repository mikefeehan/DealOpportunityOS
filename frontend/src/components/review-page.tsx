"use client";

import { CheckCircle2, FileSpreadsheet, RefreshCw, Trash2, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { confirmMatch, getReviewQueue, importUniverse, rejectRecord } from "@/lib/api";
import type { ImportSummary, ReviewQueue, ReviewRecord } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeading } from "@/components/page-heading";

const STATUS_TONE: Record<string, "green" | "amber" | "red" | "default"> = {
  verified: "green",
  needs_review: "amber",
  no_match: "red"
};

const STATUS_LABEL: Record<string, string> = {
  verified: "Verified",
  needs_review: "Needs Review",
  no_match: "No Parcel Match"
};

function MatchBadge({ status }: { status: string }) {
  return <Badge tone={STATUS_TONE[status] ?? "default"}>{STATUS_LABEL[status] ?? status}</Badge>;
}

function ImportPanel({ onImported }: { onImported: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [enrichParcels, setEnrichParcels] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ImportSummary | null>(null);

  async function submit() {
    if (!file) return;
    setBusy(true);
    setResult(null);
    const summary = await importUniverse(file, sourceName, enrichParcels);
    setResult(summary);
    setBusy(false);
    if (summary.status === "ok") {
      onImported();
    }
  }

  return (
    <Card className="border-amber/30 bg-[#11100c]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet size={16} className="text-amber" />
          Import Real Universe
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <p className="text-muted">
          Upload a manual CSV or XLSX export (HelloData, Yardi, RealPage, or analyst research). Required columns: a
          property name or address, and a units count. Optional: year built, rents, owner, sale year. Records are
          matched against Pima County parcels and land in the review queue below &mdash; they never enter the real call
          list until you confirm the match.
        </p>
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <div>
            <label className="text-xs uppercase text-muted">Source label</label>
            <Input
              className="mt-1"
              placeholder="e.g. HelloData Tucson export"
              value={sourceName}
              onChange={(e) => setSourceName(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-muted">File (.csv / .xlsx)</label>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xlsm"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm text-muted file:mr-3 file:rounded-md file:border file:border-border file:bg-panel2 file:px-3 file:py-1.5 file:text-sm file:text-ink hover:file:border-amber/50"
            />
          </div>
          <Button onClick={submit} disabled={!file || busy}>
            <Upload size={15} className={busy ? "animate-pulse" : ""} />
            {busy ? "Importing" : "Import"}
          </Button>
        </div>
        <label className="mt-1 flex items-center gap-2 text-xs text-muted">
          <input type="checkbox" checked={enrichParcels} onChange={(e) => setEnrichParcels(e.target.checked)} />
          Match each record to a Pima County parcel on import (slower — best for small files; large files import fast and can be matched per-record later).
        </label>

        {result && result.status === "error" && (
          <div className="rounded-md border border-red/35 bg-red/10 p-3 text-red">
            <div className="font-medium">Import failed</div>
            <div className="mt-1 text-xs">{result.error}</div>
            {result.detected_columns && (
              <div className="mt-2 text-xs text-muted">Detected columns: {result.detected_columns.join(", ")}</div>
            )}
          </div>
        )}

        {result && result.status === "ok" && (
          <div className="rounded-md border border-border bg-panel2 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="green">{result.imported} imported</Badge>
              <Badge tone="amber">{result.needs_review ?? 0} need review</Badge>
              <Badge tone="red">{result.no_match ?? 0} no match</Badge>
              {result.skipped ? <Badge tone="default">{result.skipped} skipped</Badge> : null}
              {result.demos_removed ? <Badge tone="default">{result.demos_removed} demos removed</Badge> : null}
              <span className="text-xs text-muted">from {result.rows_seen} rows</span>
            </div>
            {result.skipped_reasons && result.skipped_reasons.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-xs text-muted">
                {result.skipped_reasons.map((reason) => (
                  <li key={reason}>- {reason}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ReviewRow({
  record,
  onConfirm,
  onReject,
  pending
}: {
  record: ReviewRecord;
  onConfirm: (id: number) => void;
  onReject: (id: number) => void;
  pending: boolean;
}) {
  return (
    <tr className="border-b border-border align-top hover:bg-panel2/70">
      <td className="px-3 py-3">
        <div className="font-medium text-ink">{record.name}</div>
        <div className="mt-0.5 text-xs text-muted">{record.address}</div>
        <div className="mt-1 text-xs text-muted">Source: {record.source_name || record.source}</div>
      </td>
      <td className="px-3 py-3 text-sm text-ink">{record.units}</td>
      <td className="px-3 py-3 text-sm text-ink">{record.year_built || "—"}</td>
      <td className="px-3 py-3 text-sm">
        <div className="text-ink">{record.owner_name}</div>
        <div className="text-xs text-muted">{record.owner_state || "—"}</div>
      </td>
      <td className="px-3 py-3">
        <MatchBadge status={record.match_status} />
        <div className="mt-1 text-xs text-muted">
          {record.match_status === "no_match"
            ? `Parcel ${record.parcel_id}`
            : `Confidence ${(record.match_confidence * 100).toFixed(0)}%`}
        </div>
      </td>
      <td className="px-3 py-3">
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={record.match_status === "no_match" ? "secondary" : "default"}
            onClick={() => onConfirm(record.id)}
            disabled={pending}
            title={
              record.match_status === "no_match"
                ? "No auto parcel match — confirm only if you manually verified this owner/parcel"
                : "Confirm parcel match and promote to the real call list"
            }
          >
            <CheckCircle2 size={14} />
            {record.match_status === "no_match" ? "Verify anyway" : "Confirm"}
          </Button>
          <Button size="sm" variant="danger" onClick={() => onReject(record.id)} disabled={pending}>
            <Trash2 size={14} />
            Reject
          </Button>
        </div>
      </td>
    </tr>
  );
}

export function ReviewPage() {
  const [queue, setQueue] = useState<ReviewQueue | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const data = await getReviewQueue();
    setQueue(data);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleConfirm(id: number) {
    setPendingId(id);
    await confirmMatch(id);
    await refresh();
    setPendingId(null);
  }

  async function handleReject(id: number) {
    setPendingId(id);
    await rejectRecord(id);
    await refresh();
    setPendingId(null);
  }

  const records = queue?.records ?? [];

  return (
    <div>
      <PageHeading eyebrow="Data Pipeline" title="Import & Review Queue">
        <Button variant="secondary" onClick={refresh} disabled={loading}>
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          Refresh
        </Button>
      </PageHeading>

      <div className="grid gap-4">
        <ImportPanel onImported={refresh} />

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Review Queue</CardTitle>
            <div className="flex gap-2">
              <Badge tone="amber">{queue?.needs_review ?? 0} need review</Badge>
              <Badge tone="red">{queue?.no_match ?? 0} no match</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-sm text-muted">
              Confirm a parcel match to promote a record to <span className="text-green">Verified</span> &mdash; only
              verified records appear in the real call list. Reject to remove a bad import.
            </p>
            {records.length === 0 ? (
              <div className="rounded-md border border-dashed border-border bg-panel2 p-6 text-center text-sm text-muted">
                {loading ? "Loading review queue..." : "Nothing to review. Import an export above to populate the queue."}
              </div>
            ) : (
              <div className="overflow-x-auto scrollbar-thin">
                <table className="w-full min-w-[860px] border-collapse text-left">
                  <thead className="bg-panel2 text-xs uppercase text-muted">
                    <tr>
                      <th className="px-3 py-2">Property</th>
                      <th className="px-3 py-2">Units</th>
                      <th className="px-3 py-2">Built</th>
                      <th className="px-3 py-2">Owner</th>
                      <th className="px-3 py-2">Match</th>
                      <th className="px-3 py-2">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <ReviewRow
                        key={record.id}
                        record={record}
                        onConfirm={handleConfirm}
                        onReject={handleReject}
                        pending={pendingId === record.id}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
