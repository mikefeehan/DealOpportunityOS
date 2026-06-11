import {
  fallbackPipeline,
  fallbackProperty,
  fallbackSummary,
  fallbackToday
} from "./fallback";
import type {
  CallPrep,
  ImportSummary,
  MapPoint,
  MarketContext,
  MarketOption,
  MarketSummary,
  OwnerProfile,
  PipelinePayload,
  PropertyOpportunity,
  ReviewQueue,
  TodayCallList
} from "./types";

// Default to IPv4 explicitly. On Windows, "localhost" often resolves to IPv6
// (::1) first, but the backend binds to IPv4 (127.0.0.1) — so a "localhost"
// base makes every request fail (GETs silently fall back, uploads surface
// "Failed to fetch"). Override with NEXT_PUBLIC_API_BASE when needed.
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
export const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

const MARKET_KEY = "oos.selectedMarket";

export function getSelectedMarket(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(MARKET_KEY) || "";
}

export function setSelectedMarket(market: string) {
  if (typeof window === "undefined") return;
  if (market) window.localStorage.setItem(MARKET_KEY, market);
  else window.localStorage.removeItem(MARKET_KEY);
}

function withMarket(params: URLSearchParams) {
  const market = getSelectedMarket();
  if (market) params.set("market", market);
  return params;
}

export function exportUrl(path: string) {
  return `${API_BASE}${path}`;
}

async function fetchJson<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {})
      }
    });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function getTodayCallList(dataScope?: string) {
  const params = new URLSearchParams();
  if (dataScope) params.set("data_scope", dataScope);
  withMarket(params);
  const query = params.toString();
  return fetchJson<TodayCallList>(`/api/today-call-list${query ? `?${query}` : ""}`, fallbackToday);
}

export function getSummary() {
  const query = withMarket(new URLSearchParams()).toString();
  return fetchJson<MarketSummary>(`/api/market/summary${query ? `?${query}` : ""}`, fallbackSummary);
}

export function getMarkets() {
  return fetchJson<MarketOption[]>("/api/markets", []);
}

export function getMapPoints(dataScope?: string) {
  const params = new URLSearchParams();
  if (dataScope) params.set("data_scope", dataScope);
  withMarket(params);
  const query = params.toString();
  return fetchJson<MapPoint[]>(`/api/map${query ? `?${query}` : ""}`, []);
}

export function getMarketContext() {
  return fetchJson<MarketContext>("/api/market/context", {
    available: false,
    as_of: null,
    source: "HelloData Market Analytics",
    rent: {},
    supply: {},
    demographics: {},
    comp_set: {}
  });
}

export function getOwners(intrustMode = false, limit?: number) {
  const params = new URLSearchParams();
  params.set("intrust_mode", String(intrustMode));
  if (limit) params.set("limit", String(limit));
  withMarket(params);
  return fetchJson<OwnerProfile[]>(`/api/owners?${params.toString()}`, [fallbackToday.top_10_owners[0]]);
}

export function getOwner(ownerName: string) {
  return fetchJson<OwnerProfile>(`/api/owners/${encodeURIComponent(ownerName)}`, fallbackToday.top_10_owners[0]);
}

export function getOpportunities(params: Record<string, string | number | boolean | undefined> = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") search.set(key, String(value));
  });
  withMarket(search);
  return fetchJson<PropertyOpportunity[]>(`/api/opportunities?${search.toString()}`, fallbackToday.top_25_properties);
}

export function getProperty(id: string) {
  return fetchJson<PropertyOpportunity>(`/api/properties/${id}`, fallbackProperty);
}

export function getPipeline() {
  return fetchJson<PipelinePayload>("/api/pipeline", fallbackPipeline);
}

export function scanTucson() {
  return fetchJson<{ fallback_active: boolean; total_properties: number; live_records_imported: number }>(
    "/api/scan/tucson",
    { fallback_active: true, total_properties: 1, live_records_imported: 0 },
    { method: "POST" }
  );
}

export function updatePipeline(propertyId: number, payload: { stage?: string; notes?: string }) {
  return fetchJson(`/api/pipeline/${propertyId}`, payload, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getReviewQueue(includeVerified = false) {
  const params = new URLSearchParams();
  if (includeVerified) params.set("include_verified", "true");
  const query = params.toString();
  return fetchJson<ReviewQueue>(
    `/api/review-queue${query ? `?${query}` : ""}`,
    { total: 0, needs_review: 0, no_match: 0, verified: 0, records: [] }
  );
}

export async function importUniverse(file: File, sourceName: string, enrichParcels = false): Promise<ImportSummary> {
  const form = new FormData();
  form.append("file", file);
  form.append("source_name", sourceName);
  form.append("enrich_parcels", String(enrichParcels));
  try {
    const response = await fetch(`${API_BASE}/api/import/universe`, { method: "POST", body: form });
    const body = (await response.json().catch(() => null)) as ImportSummary | { detail?: string } | null;
    if (!response.ok) {
      const detail = (body && "detail" in body && body.detail) || `${response.status} ${response.statusText}`;
      return { status: "error", error: String(detail), rows_seen: 0, imported: 0 };
    }
    return (body as ImportSummary) ?? { status: "error", error: "Empty response", rows_seen: 0, imported: 0 };
  } catch (err) {
    return { status: "error", error: String(err), rows_seen: 0, imported: 0 };
  }
}

export function confirmMatch(propertyId: number) {
  return fetchJson(`/api/review/${propertyId}/confirm`, { id: propertyId }, { method: "POST" });
}

export function rejectRecord(propertyId: number) {
  return fetchJson(`/api/review/${propertyId}/reject`, { id: propertyId }, { method: "POST" });
}

export function generateCallPrep(ownerName: string) {
  return fetchJson<CallPrep>(
    "/api/ai/call-prep",
    {
      source: "frontend_fallback",
      why_owner_may_sell: "Long hold with potential embedded gain.",
      opening_call_line: "I am calling from InTrust to discuss a quiet off-market conversation.",
      talking_points: ["Long-term ownership", "Potential tax-efficient exit", "Below-market rent signal"],
      possible_objections: ["Not ready to sell", "Tax concerns", "Needs price certainty"],
      exchange_721_angle: "Discuss 721 exchange only if tax friction is a priority."
    },
    {
      method: "POST",
      body: JSON.stringify({ owner_name: ownerName })
    }
  );
}
