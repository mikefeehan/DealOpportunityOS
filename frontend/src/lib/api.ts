import {
  fallbackPipeline,
  fallbackProperty,
  fallbackSummary,
  fallbackToday
} from "./fallback";
import type {
  CallPrep,
  MarketSummary,
  OwnerProfile,
  PipelinePayload,
  PropertyOpportunity,
  TodayCallList
} from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

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

export function getTodayCallList() {
  return fetchJson<TodayCallList>("/api/today-call-list", fallbackToday);
}

export function getSummary() {
  return fetchJson<MarketSummary>("/api/market/summary", fallbackSummary);
}

export function getOwners(intrustMode = false, limit?: number) {
  const params = new URLSearchParams();
  params.set("intrust_mode", String(intrustMode));
  if (limit) params.set("limit", String(limit));
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
