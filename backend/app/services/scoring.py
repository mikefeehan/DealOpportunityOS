from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from backend.app.models import Property


ACQUISITION_WEIGHTS = {
    "hold_period": 0.25,
    "rent_upside": 0.20,
    "ownership_type": 0.15,
    "owner_distance": 0.10,
    "vintage": 0.10,
    "basis_gap": 0.10,
    "contactability": 0.10,
}

TARGET_OWNER_STATES = {"AZ", "CA", "NV", "UT", "CO"}
INTRUST_MODE_OWNER_STATES = {"AZ", "CA", "NV"}
PIPELINE_STAGES = ["Identified", "Research", "Contacted", "Meeting", "LOI", "Dead", "Closed"]


@dataclass(frozen=True)
class ScoreResult:
    acquisition_score: float
    fit_score: float
    motivation_score: float
    call_score: float
    hold_period: float
    rent_gap: float
    basis_gap: float
    ownership_type_score: float
    owner_distance_score: float
    contactability_score: float
    hold_period_score: float
    rent_gap_score: float
    vintage_score: float
    basis_gap_score: float
    units_score: float
    private_owner_score: float
    recommendation: str
    potential_721_candidate: bool
    estimated_tax_deferral: float


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def is_institutional_owner(owner_name: str) -> bool:
    owner = owner_name.upper()
    return any(token in owner for token in ["REIT", "INSTITUTIONAL", "FUND IV", "FUND V", "BLACKSTONE", "GREYSTAR"])


def is_private_owner(owner_name: str) -> bool:
    owner = owner_name.upper()
    if is_institutional_owner(owner):
        return False
    return any(
        token in owner
        for token in ["LLC", "LP", "L.P.", "PARTNERS", "HOLDINGS", "FAMILY", "ESTATE", "TRUST", "APARTMENTS"]
    )


def is_721_owner_type(owner_name: str) -> bool:
    owner = owner_name.upper()
    return is_private_owner(owner) and any(
        token in owner for token in ["LLC", "LP", "L.P.", "PARTNERS", "FAMILY", "ESTATE", "TRUST", "APARTMENTS"]
    )


def score_hold_period(years: float) -> float:
    if years < 5:
        return 12
    if years < 10:
        return 35
    if years < 15:
        return 58
    if years < 25:
        return 82
    return 96


def score_rent_gap(rent_gap: float) -> float:
    return clamp(rent_gap * 2.4)


def score_basis_gap(basis_gap: float) -> float:
    return clamp(basis_gap * 2.2)


def score_units(units: int) -> float:
    if units < 50:
        return 0
    if units < 75:
        return 48
    if units <= 250:
        return 96
    if units <= 400:
        return 82
    return 62


def score_ownership_type(owner_name: str) -> float:
    owner = owner_name.upper()
    if is_institutional_owner(owner):
        return 20
    if any(token in owner for token in ["TRUST", "FAMILY", "ESTATE"]):
        return 95
    if any(token in owner for token in ["LLC", "LP", "L.P.", "PARTNERS", "HOLDINGS", "APARTMENTS"]):
        return 84
    if any(token in owner for token in ["NONPROFIT", "HOUSING AUTHORITY", "CITY OF"]):
        return 18
    return 68


def score_owner_distance(owner_state: str, owner_city: str) -> float:
    state = (owner_state or "").upper()
    city = (owner_city or "").upper()
    if state in {"CA", "NV"}:
        return 94
    if state in {"UT", "CO"}:
        return 84
    if state and state != "AZ":
        return 72
    if city and city not in {"TUCSON", "ORO VALLEY", "MARANA", "SAHUARITA"}:
        return 66
    return 34


def score_vintage(year_built: int) -> float:
    if year_built < 1960:
        return 58
    if 1970 <= year_built <= 2015:
        return 96
    if 1960 <= year_built < 1970:
        return 82
    if 2016 <= year_built <= 2020:
        return 30
    if year_built > 2020:
        return 14
    return 70


def score_contactability(mailing_address: str, owner_name: str) -> float:
    score = 35
    if mailing_address and len(mailing_address) > 12:
        score += 34
    if any(token in owner_name.upper() for token in ["LLC", "LP", "PARTNERS", "HOLDINGS", "TRUST", "FAMILY"]):
        score += 15
    if any(char.isdigit() for char in mailing_address):
        score += 10
    return clamp(score)


def calculate_market_value(prop: Property) -> float:
    if not prop.units or not prop.market_rent:
        return prop.assessed_value
    income_value_per_unit = (prop.market_rent * 12 / 0.0625) * 0.82
    return max(prop.assessed_value, income_value_per_unit * prop.units)


def calculate_basis_gap(prop: Property) -> float:
    if not prop.units:
        return 0
    market_value = calculate_market_value(prop)
    if market_value <= 0:
        return 0
    return clamp((market_value - prop.assessed_value) / market_value * 100, 0, 55)


def estimate_tax_deferral(prop: Property, basis_gap: float) -> float:
    market_value = calculate_market_value(prop)
    embedded_gain = max(0, market_value - prop.assessed_value)
    if basis_gap < 8:
        return 0
    return round(embedded_gain * 0.28, 0)


def calculate_fit_score(
    units_score: float,
    vintage_score: float,
    rent_gap_score: float,
    basis_gap_score: float,
    owner_state: str,
    year_built: int,
) -> float:
    market_score = 100
    state = (owner_state or "").upper()
    if state and state not in TARGET_OWNER_STATES:
        market_score = 70
    luxury_penalty = 18 if year_built > 2018 else 0
    score = (
        units_score * 0.30
        + vintage_score * 0.20
        + rent_gap_score * 0.25
        + basis_gap_score * 0.15
        + market_score * 0.10
        - luxury_penalty
    )
    return round(clamp(score), 1)


def calculate_motivation_score(
    hold_period_score: float,
    ownership_type_score: float,
    owner_distance_score: float,
    contactability_score: float,
    potential_721: bool,
    recent_trade: bool,
) -> float:
    score = (
        hold_period_score * 0.34
        + ownership_type_score * 0.24
        + owner_distance_score * 0.18
        + contactability_score * 0.14
        + (100 if potential_721 else 45) * 0.10
    )
    if recent_trade:
        score -= 24
    return round(clamp(score), 1)


def recommendation_for(call_score: float, fit_score: float, motivation_score: float, potential_721: bool) -> str:
    if call_score >= 88.5 and fit_score >= 86 and motivation_score >= 87:
        return "Call Owner"
    if potential_721 and call_score >= 90:
        return "Call Owner"
    if call_score >= 58:
        return "Monitor"
    return "Ignore"


def calculate_score(prop: Property, current_year: int | None = None) -> ScoreResult:
    year = current_year or date.today().year
    hold_period = max(0, year - (prop.last_sale_year or year))
    rent_gap = 0.0
    if prop.market_rent:
        rent_gap = clamp((prop.market_rent - prop.average_rent) / prop.market_rent * 100, 0, 55)
    basis_gap = calculate_basis_gap(prop)

    hold_period_score = score_hold_period(hold_period)
    rent_gap_score = score_rent_gap(rent_gap)
    basis_gap_score = score_basis_gap(basis_gap)
    ownership_type_score = score_ownership_type(prop.owner_name)
    owner_distance_score = score_owner_distance(prop.owner_state, prop.owner_city)
    vintage_score = score_vintage(prop.year_built)
    contactability_score = score_contactability(prop.mailing_address, prop.owner_name)
    units_score = score_units(prop.units)
    private_owner_score = 100 if is_private_owner(prop.owner_name) else 20

    weighted_acquisition = (
        hold_period_score * ACQUISITION_WEIGHTS["hold_period"]
        + rent_gap_score * ACQUISITION_WEIGHTS["rent_upside"]
        + ownership_type_score * ACQUISITION_WEIGHTS["ownership_type"]
        + owner_distance_score * ACQUISITION_WEIGHTS["owner_distance"]
        + vintage_score * ACQUISITION_WEIGHTS["vintage"]
        + basis_gap_score * ACQUISITION_WEIGHTS["basis_gap"]
        + contactability_score * ACQUISITION_WEIGHTS["contactability"]
    )

    estimated_tax_deferral = estimate_tax_deferral(prop, basis_gap)
    potential_721 = bool(hold_period > 15 and basis_gap > 12 and is_721_owner_type(prop.owner_name))
    recent_trade = hold_period < 5

    fit_score = calculate_fit_score(
        units_score=units_score,
        vintage_score=vintage_score,
        rent_gap_score=rent_gap_score,
        basis_gap_score=basis_gap_score,
        owner_state=prop.owner_state,
        year_built=prop.year_built,
    )
    motivation_score = calculate_motivation_score(
        hold_period_score=hold_period_score,
        ownership_type_score=ownership_type_score,
        owner_distance_score=owner_distance_score,
        contactability_score=contactability_score,
        potential_721=potential_721,
        recent_trade=recent_trade,
    )
    call_score = round((fit_score * 0.5) + (motivation_score * 0.5), 1)
    recommendation = recommendation_for(call_score, fit_score, motivation_score, potential_721)

    return ScoreResult(
        acquisition_score=round(weighted_acquisition, 1),
        fit_score=fit_score,
        motivation_score=motivation_score,
        call_score=call_score,
        hold_period=round(hold_period, 1),
        rent_gap=round(rent_gap, 1),
        basis_gap=round(basis_gap, 1),
        ownership_type_score=round(ownership_type_score, 1),
        owner_distance_score=round(owner_distance_score, 1),
        contactability_score=round(contactability_score, 1),
        hold_period_score=round(hold_period_score, 1),
        rent_gap_score=round(rent_gap_score, 1),
        vintage_score=round(vintage_score, 1),
        basis_gap_score=round(basis_gap_score, 1),
        units_score=round(units_score, 1),
        private_owner_score=round(private_owner_score, 1),
        recommendation=recommendation,
        potential_721_candidate=potential_721,
        estimated_tax_deferral=estimated_tax_deferral,
    )


def why_now_for_property(prop: Property, score: Any) -> str:
    reasons: list[str] = []
    if score.hold_period >= 15:
        reasons.append(f"Held {score.hold_period:.0f} years")
    state = (prop.owner_state or "").upper()
    if state and state != "AZ":
        reasons.append(f"{state} owner")
    if score.basis_gap >= 15:
        reasons.append("significant embedded gain")
    if score.potential_721_candidate:
        reasons.append("potential 721 candidate")
    if score.rent_gap >= 18:
        reasons.append("below-market rents")
    if 1970 <= prop.year_built <= 1995:
        reasons.append("vintage asset")
    if not reasons:
        reasons.append("moderate fit but lower owner motivation")
    return ". ".join(reasons[:5]) + "."


def recommended_angle_for_property(prop: Property, score: Any) -> str:
    if score.potential_721_candidate:
        return "Lead with a tax-efficient 721 exchange conversation and liquidity without forcing a taxable sale."
    if score.hold_period >= 20 and score.rent_gap >= 18:
        return "Lead with legacy ownership, operational lift, and a quiet off-market path that protects certainty."
    if (prop.owner_state or "").upper() != "AZ":
        return "Lead with local execution, reduced remote-management burden, and a confidential valuation read."
    if score.recommendation == "Monitor":
        return "Track ownership signals and ask for a soft portfolio conversation before broker engagement."
    return "Low-conviction fit today; keep out of the call queue unless new motivation signals appear."


def score_breakdown(score: Any) -> list[dict[str, Any]]:
    return [
        {
            "factor": "Hold Period",
            "weight": 25,
            "score": score.hold_period_score,
            "raw": f"{score.hold_period:.1f} years",
        },
        {
            "factor": "Rent Upside",
            "weight": 20,
            "score": score.rent_gap_score,
            "raw": f"{score.rent_gap:.1f}% gap",
        },
        {
            "factor": "Ownership Type",
            "weight": 15,
            "score": score.ownership_type_score,
            "raw": "private/family/trust signal",
        },
        {
            "factor": "Owner Distance",
            "weight": 10,
            "score": score.owner_distance_score,
            "raw": "mailing market distance",
        },
        {
            "factor": "Vintage",
            "weight": 10,
            "score": score.vintage_score,
            "raw": "InTrust vintage fit",
        },
        {
            "factor": "Basis Gap",
            "weight": 10,
            "score": score.basis_gap_score,
            "raw": f"{score.basis_gap:.1f}% gap",
        },
        {
            "factor": "Contactability",
            "weight": 10,
            "score": score.contactability_score,
            "raw": "mailing data quality",
        },
    ]
