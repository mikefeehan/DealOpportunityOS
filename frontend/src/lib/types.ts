export type ScoreBreakdown = {
  factor: string;
  weight: number;
  score: number;
  raw: string;
};

export type PropertyOpportunity = {
  id: number;
  parcel_id: string;
  name: string;
  address: string;
  units: number;
  year_built: number;
  building_sqft: number;
  assessed_value: number;
  owner_name: string;
  mailing_address: string;
  owner_city: string;
  owner_state: string;
  latitude: number;
  longitude: number;
  property_type: string;
  submarket: string;
  source: string;
  source_name: string;
  source_url: string;
  data_status: "seeded_fallback" | "live_authorized" | "live_public" | string;
  match_status: "verified" | "needs_review" | "no_match" | string;
  match_confidence: number;
  matched_address: string;
  last_verified_at: string | null;
  last_sale_year: number;
  average_rent: number;
  market_rent: number;
  stage: string;
  notes: string;
  acquisition_score: number;
  fit_score: number;
  motivation_score: number;
  call_score: number;
  hold_period: number;
  rent_gap: number;
  basis_gap: number;
  recommendation: "Ignore" | "Monitor" | "Call Owner" | string;
  potential_721_candidate: boolean;
  estimated_tax_deferral: number;
  why_now: string;
  recommended_angle: string;
  score_breakdown: ScoreBreakdown[];
};

export type OwnerProfile = {
  rank: number;
  owner: string;
  data_status: string;
  mailing_address: string;
  owner_city: string;
  owner_state: string;
  properties_owned: number;
  units_owned: number;
  estimated_portfolio_value: number;
  average_hold_period: number;
  oldest_acquisition: number;
  newest_acquisition: number;
  average_rent_gap: number;
  acquisition_score: number;
  fit_score: number;
  motivation_score: number;
  call_score: number;
  outreach_score: number;
  potential_721_candidate: boolean;
  estimated_tax_deferral: number;
  recommendation: string;
  top_property: PropertyOpportunity;
  properties: PropertyOpportunity[];
  why_now: string;
  recommended_angle: string;
};

export type MarketSummary = {
  market: string;
  total_properties: number;
  total_owners: number;
  high_score_targets: number;
  long_hold_owners: number;
  average_hold_period: number;
  average_rent_gap: number;
  average_call_score: number;
  potential_721_candidates: number;
  data_provenance: {
    mode: string;
    live_records: number;
    verified_live_records: number;
    needs_review_records: number;
    fallback_records: number;
    source_counts: Record<string, number>;
    disclaimer: string;
  };
  reporting: {
    owners_researched: number;
    owners_contacted: number;
    meetings_generated: number;
    off_market_opportunities: number;
    lois_submitted: number;
    deals_closed: number;
  };
  pipeline: Record<string, number>;
};

export type TodayCallList = {
  top_10_owners: OwnerProfile[];
  top_25_owners: OwnerProfile[];
  top_25_properties: PropertyOpportunity[];
  top_new_opportunities: PropertyOpportunity[];
};

export type PipelinePayload = {
  stages: string[];
  properties_by_stage: Record<string, PropertyOpportunity[]>;
};

export type CallPrep = {
  source: string;
  why_owner_may_sell: string;
  opening_call_line: string;
  talking_points: string[];
  possible_objections: string[];
  exchange_721_angle: string;
};

export type ReviewRecord = {
  id: number;
  parcel_id: string;
  name: string;
  address: string;
  units: number;
  year_built: number;
  owner_name: string;
  owner_state: string;
  mailing_address: string;
  source: string;
  source_name: string;
  data_status: string;
  match_status: "verified" | "needs_review" | "no_match" | string;
  match_confidence: number;
  matched_address: string;
  call_score: number;
  recommendation: string;
  last_verified_at: string | null;
};

export type ReviewQueue = {
  total: number;
  needs_review: number;
  no_match: number;
  verified: number;
  records: ReviewRecord[];
};

export type ImportSummary = {
  status: "ok" | "error" | string;
  error?: string;
  filename?: string;
  source_name?: string;
  rows_seen: number;
  imported: number;
  needs_review?: number;
  verified?: number;
  no_match?: number;
  skipped?: number;
  skipped_reasons?: string[];
  detected_columns?: string[];
  column_map?: Record<string, string>;
  sample?: { name: string; address: string; units: number; match_status: string; parcel_id: string }[];
};
