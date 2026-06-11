import type { MarketSummary, OwnerProfile, PipelinePayload, PropertyOpportunity, TodayCallList } from "./types";

export const fallbackProperty: PropertyOpportunity = {
  id: 1,
  parcel_id: "SEED-TUC-0001",
  name: "Palo Verde Vista",
  address: "1485 E Fort Lowell Rd, Tucson, AZ 85719",
  units: 124,
  year_built: 1973,
  building_sqft: 108500,
  assessed_value: 8950000,
  owner_name: "Desert Ridge Multifamily LLC",
  mailing_address: "433 N Camden Dr Ste 640, Beverly Hills, CA 90210",
  owner_city: "Beverly Hills",
  owner_state: "CA",
  latitude: 32.2654,
  longitude: -110.9482,
  property_type: "Apartments",
  submarket: "Central Tucson",
  source: "Frontend fallback preview",
  source_name: "Frontend fallback preview",
  source_url: "",
  data_status: "seeded_fallback",
  match_status: "no_match",
  match_confidence: 0,
  matched_address: "",
  last_verified_at: null,
  last_sale_year: 1999,
  average_rent: 965,
  market_rent: 1295,
  stage: "Identified",
  notes: "",
  acquisition_score: 84,
  fit_score: 86,
  motivation_score: 88,
  call_score: 87,
  hold_period: 27,
  rent_gap: 25.5,
  basis_gap: 24,
  recommendation: "Call Owner",
  potential_721_candidate: true,
  estimated_tax_deferral: 1800000,
  why_now: "Held 27 years. CA owner. Significant embedded gain. Potential 721 candidate. Below-market rents.",
  recommended_angle: "Lead with a tax-efficient 721 exchange conversation and liquidity without forcing a taxable sale.",
  score_breakdown: []
};

export const fallbackOwner: OwnerProfile = {
  rank: 1,
  owner: "Desert Ridge Multifamily LLC",
  data_status: "seeded_fallback",
  mailing_address: fallbackProperty.mailing_address,
  owner_city: "Beverly Hills",
  owner_state: "CA",
  properties_owned: 1,
  units_owned: 124,
  estimated_portfolio_value: 13200000,
  average_hold_period: 27,
  oldest_acquisition: 1999,
  newest_acquisition: 1999,
  average_rent_gap: 25.5,
  acquisition_score: 84,
  fit_score: 86,
  motivation_score: 88,
  call_score: 87,
  outreach_score: 88,
  potential_721_candidate: true,
  estimated_tax_deferral: 1800000,
  recommendation: "Call Owner",
  top_property: fallbackProperty,
  properties: [fallbackProperty],
  why_now: fallbackProperty.why_now,
  recommended_angle: fallbackProperty.recommended_angle
};

export const fallbackSummary: MarketSummary = {
  market: "Tucson, Arizona",
  total_properties: 1,
  total_owners: 1,
  high_score_targets: 1,
  long_hold_owners: 1,
  average_hold_period: 27,
  average_rent_gap: 25.5,
  average_call_score: 87,
  potential_721_candidates: 1,
  data_provenance: {
    mode: "Frontend fallback preview",
    live_records: 0,
    verified_live_records: 0,
    needs_review_records: 0,
    fallback_records: 1,
    source_counts: { "Frontend fallback preview": 1 },
    disclaimer: "Fallback preview records are not verified real acquisition opportunities."
  },
  reporting: {
    owners_researched: 0,
    owners_contacted: 0,
    meetings_generated: 0,
    off_market_opportunities: 0,
    lois_submitted: 0,
    deals_closed: 0
  },
  pipeline: { Identified: 1, Research: 0, Contacted: 0, Meeting: 0, LOI: 0, Dead: 0, Closed: 0 }
};

export const fallbackToday: TodayCallList = {
  top_10_owners: [fallbackOwner],
  top_25_owners: [fallbackOwner],
  top_25_properties: [fallbackProperty],
  top_new_opportunities: [fallbackProperty]
};

export const fallbackPipeline: PipelinePayload = {
  stages: ["Identified", "Research", "Contacted", "Meeting", "LOI", "Dead", "Closed"],
  properties_by_stage: { Identified: [fallbackProperty], Research: [], Contacted: [], Meeting: [], LOI: [], Dead: [], Closed: [] }
};
