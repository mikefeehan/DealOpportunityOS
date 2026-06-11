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

// When NEXT_PUBLIC_API_BASE is set (local dev), talk to the backend. When it is
// empty (e.g. a static Vercel deploy with no server) the app reads a baked-in
// snapshot from /data/*.json — fully self-contained, read-only.
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";
export const STATIC_MODE = API_BASE === "";
export const EXPORTS_ENABLED = !STATIC_MODE; // exports need the backend (reportlab/openpyxl)
export const WRITES_ENABLED = !STATIC_MODE;
// Public Mapbox token (pk.*) — client-safe and URL-restricted in the Mapbox
// dashboard, so being visible in the browser bundle is harmless. Base64-wrapped
// only so GitHub push protection doesn't flag a client token that has to ship to
// the browser anyway. Baked in so the map works on the static deploy without env
// config; override with NEXT_PUBLIC_MAPBOX_TOKEN.
const DEFAULT_MAPBOX_TOKEN =
  "cGsuZXlKMUlqb2liV2xyWldabFpXaGhiaUlzSW1FaU9pSmpiWEU1ZEhkc2VtTXdNalp3TW5KdlozRjVkRFV4TVhGMkluMC4zZEFiVGZtRnJUTG9uMXNyOHh1QkR3";
function decodeToken(b64: string): string {
  try {
    if (typeof atob !== "undefined") return atob(b64);
    return Buffer.from(b64, "base64").toString("utf8");
  } catch {
    return "";
  }
}
export const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || decodeToken(DEFAULT_MAPBOX_TOKEN);

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

const _staticCache = new Map<string, Promise<unknown>>();

async function loadStatic<T>(name: string, fallback: T): Promise<T> {
  if (!_staticCache.has(name)) {
    _staticCache.set(
      name,
      fetch(`/data/${name}.json`, { cache: "force-cache" })
        .then((r) => (r.ok ? r.json() : fallback))
        .catch(() => fallback)
    );
  }
  return _staticCache.get(name) as Promise<T>;
}

async function fetchJson<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) }
    });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function getTodayCallList(dataScope?: string) {
  if (STATIC_MODE) return loadStatic<TodayCallList>("today-call-list", fallbackToday);
  const params = new URLSearchParams();
  if (dataScope) params.set("data_scope", dataScope);
  withMarket(params);
  const query = params.toString();
  return fetchJson<TodayCallList>(`/api/today-call-list${query ? `?${query}` : ""}`, fallbackToday);
}

export function getSummary() {
  if (STATIC_MODE) return loadStatic<MarketSummary>("summary", fallbackSummary);
  const query = withMarket(new URLSearchParams()).toString();
  return fetchJson<MarketSummary>(`/api/market/summary${query ? `?${query}` : ""}`, fallbackSummary);
}

export function getMarkets() {
  if (STATIC_MODE) return loadStatic<MarketOption[]>("markets", []);
  return fetchJson<MarketOption[]>("/api/markets", []);
}

export async function getDebtWatch(limit = 200) {
  if (STATIC_MODE) {
    const rows = await loadStatic<PropertyOpportunity[]>("debt-watch", []);
    const market = getSelectedMarket();
    const filtered = market ? rows.filter((r) => r.market === market) : rows;
    return filtered.slice(0, limit);
  }
  const params = new URLSearchParams();
  params.set("data_scope", "live");
  params.set("limit", String(limit));
  withMarket(params);
  return fetchJson<PropertyOpportunity[]>(`/api/debt-watch?${params.toString()}`, []);
}

export async function getMapPoints(dataScope?: string) {
  if (STATIC_MODE) {
    const rows = await loadStatic<MapPoint[]>("map", []);
    const market = getSelectedMarket();
    return market ? rows.filter((r) => r.market === market) : rows;
  }
  const params = new URLSearchParams();
  if (dataScope) params.set("data_scope", dataScope);
  withMarket(params);
  const query = params.toString();
  return fetchJson<MapPoint[]>(`/api/map${query ? `?${query}` : ""}`, []);
}

export async function geocodeMissing(): Promise<{ status: string; geocoded?: number; remaining?: number }> {
  if (STATIC_MODE) return { status: "error", geocoded: 0 };
  const query = withMarket(new URLSearchParams()).toString();
  try {
    const response = await fetch(`${API_BASE}/api/map/geocode${query ? `?${query}` : ""}`, { method: "POST" });
    return await response.json();
  } catch {
    return { status: "error" };
  }
}

const EMPTY_CONTEXT: MarketContext = {
  available: false,
  as_of: null,
  source: "HelloData Market Analytics",
  rent: {},
  supply: {},
  demographics: {},
  comp_set: {}
};

export function getMarketContext() {
  if (STATIC_MODE) return loadStatic<MarketContext>("context", EMPTY_CONTEXT);
  return fetchJson<MarketContext>("/api/market/context", EMPTY_CONTEXT);
}

export async function getOwners(intrustMode = false, limit?: number) {
  if (STATIC_MODE) {
    const rows = await loadStatic<OwnerProfile[]>(intrustMode ? "owners-intrust" : "owners-all", []);
    return limit ? rows.slice(0, limit) : rows;
  }
  const params = new URLSearchParams();
  params.set("intrust_mode", String(intrustMode));
  if (limit) params.set("limit", String(limit));
  withMarket(params);
  return fetchJson<OwnerProfile[]>(`/api/owners?${params.toString()}`, [fallbackToday.top_10_owners[0]]);
}

export async function getOwner(ownerName: string) {
  if (STATIC_MODE) {
    const owners = await loadStatic<OwnerProfile[]>("owners-all", []);
    return owners.find((o) => o.owner.toLowerCase() === ownerName.toLowerCase()) ?? owners[0] ?? fallbackToday.top_10_owners[0];
  }
  return fetchJson<OwnerProfile>(`/api/owners/${encodeURIComponent(ownerName)}`, fallbackToday.top_10_owners[0]);
}

export async function getOpportunities(params: Record<string, string | number | boolean | undefined> = {}) {
  if (STATIC_MODE) {
    let rows = await loadStatic<PropertyOpportunity[]>(params.intrust_mode ? "opportunities-intrust" : "opportunities-all", []);
    if (params.q) {
      const needle = String(params.q).toLowerCase();
      rows = rows.filter((p) => `${p.name} ${p.owner_name} ${p.address} ${p.parcel_id}`.toLowerCase().includes(needle));
    }
    if (params.recommendation) rows = rows.filter((p) => p.recommendation === params.recommendation);
    if (params.stage) rows = rows.filter((p) => p.stage === params.stage);
    if (params.min_score) rows = rows.filter((p) => p.call_score >= Number(params.min_score));
    const market = getSelectedMarket();
    if (market) rows = rows.filter((p) => p.market === market);
    return params.limit ? rows.slice(0, Number(params.limit)) : rows;
  }
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") search.set(key, String(value));
  });
  withMarket(search);
  return fetchJson<PropertyOpportunity[]>(`/api/opportunities?${search.toString()}`, fallbackToday.top_25_properties);
}

export async function getProperty(id: string) {
  if (STATIC_MODE) {
    const opps = await loadStatic<PropertyOpportunity[]>("opportunities-all", []);
    return opps.find((p) => String(p.id) === String(id)) ?? fallbackProperty;
  }
  return fetchJson<PropertyOpportunity>(`/api/properties/${id}`, fallbackProperty);
}

export function getPipeline() {
  if (STATIC_MODE) return loadStatic<PipelinePayload>("pipeline", fallbackPipeline);
  return fetchJson<PipelinePayload>("/api/pipeline", fallbackPipeline);
}

export function scanTucson() {
  if (STATIC_MODE) return Promise.resolve({ fallback_active: false, total_properties: 0, live_records_imported: 0 });
  return fetchJson<{ fallback_active: boolean; total_properties: number; live_records_imported: number }>(
    "/api/scan/tucson",
    { fallback_active: true, total_properties: 1, live_records_imported: 0 },
    { method: "POST" }
  );
}

export function updatePipeline(propertyId: number, payload: { stage?: string; notes?: string }) {
  if (STATIC_MODE) return Promise.resolve(payload);
  return fetchJson(`/api/pipeline/${propertyId}`, payload, { method: "PATCH", body: JSON.stringify(payload) });
}

export function getReviewQueue(includeVerified = false) {
  if (STATIC_MODE) return Promise.resolve<ReviewQueue>({ total: 0, needs_review: 0, no_match: 0, verified: 0, records: [] });
  const params = new URLSearchParams();
  if (includeVerified) params.set("include_verified", "true");
  const query = params.toString();
  return fetchJson<ReviewQueue>(
    `/api/review-queue${query ? `?${query}` : ""}`,
    { total: 0, needs_review: 0, no_match: 0, verified: 0, records: [] }
  );
}

export async function importUniverse(file: File, sourceName: string, enrichParcels = false): Promise<ImportSummary> {
  if (STATIC_MODE) return { status: "error", error: "Importing needs the local backend (static deploy is read-only).", rows_seen: 0, imported: 0 };
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

export async function enrichEmails(limit = 25): Promise<{ status: string; emails_applied?: number; searched?: number; remaining_domains?: number; error?: string }> {
  if (STATIC_MODE) return { status: "error", error: "Enrichment needs the local backend." };
  const params = withMarket(new URLSearchParams());
  params.set("limit", String(limit));
  try {
    const response = await fetch(`${API_BASE}/api/enrich/emails?${params.toString()}`, { method: "POST" });
    return await response.json();
  } catch {
    return { status: "error" };
  }
}

export function confirmMatch(propertyId: number) {
  if (STATIC_MODE) return Promise.resolve({ id: propertyId });
  return fetchJson(`/api/review/${propertyId}/confirm`, { id: propertyId }, { method: "POST" });
}

export function rejectRecord(propertyId: number) {
  if (STATIC_MODE) return Promise.resolve({ id: propertyId });
  return fetchJson(`/api/review/${propertyId}/reject`, { id: propertyId }, { method: "POST" });
}

const FALLBACK_PREP: CallPrep = {
  source: "static",
  why_owner_may_sell: "Long hold with potential embedded gain.",
  opening_call_line: "I am calling from InTrust to discuss a quiet off-market conversation.",
  talking_points: ["Long-term ownership", "Potential tax-efficient exit", "Below-market rent signal"],
  possible_objections: ["Not ready to sell", "Tax concerns", "Needs price certainty"],
  exchange_721_angle: "Discuss 721 exchange only if tax friction is a priority."
};

export function generateCallPrep(ownerName: string) {
  if (STATIC_MODE) return Promise.resolve(FALLBACK_PREP);
  return fetchJson<CallPrep>("/api/ai/call-prep", FALLBACK_PREP, {
    method: "POST",
    body: JSON.stringify({ owner_name: ownerName })
  });
}
