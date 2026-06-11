from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.models import OpportunityScore, Pipeline, Property
from backend.app.services.scoring import (
    INTRUST_MODE_OWNER_STATES,
    PIPELINE_STAGES,
    is_institutional_owner,
    is_private_owner,
    recommended_angle_for_property,
    score_breakdown,
    why_now_for_property,
)


def money(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


def property_to_dict(prop: Property) -> dict[str, Any]:
    score = prop.score
    pipeline = prop.pipeline
    return {
        "id": prop.id,
        "parcel_id": prop.parcel_id,
        "name": prop.name,
        "address": prop.address,
        "units": prop.units,
        "year_built": prop.year_built,
        "building_sqft": prop.building_sqft,
        "assessed_value": prop.assessed_value,
        "owner_name": prop.owner_name,
        "mailing_address": prop.mailing_address,
        "owner_city": prop.owner_city,
        "owner_state": prop.owner_state,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "property_type": prop.property_type,
        "submarket": prop.submarket,
        "source": prop.source,
        "last_sale_year": prop.last_sale_year,
        "average_rent": prop.average_rent,
        "market_rent": prop.market_rent,
        "stage": pipeline.stage if pipeline else "Identified",
        "notes": pipeline.notes if pipeline else "",
        "acquisition_score": score.acquisition_score if score else 0,
        "fit_score": score.fit_score if score else 0,
        "motivation_score": score.motivation_score if score else 0,
        "call_score": score.call_score if score else 0,
        "hold_period": score.hold_period if score else 0,
        "rent_gap": score.rent_gap if score else 0,
        "basis_gap": score.basis_gap if score else 0,
        "recommendation": score.recommendation if score else "Monitor",
        "potential_721_candidate": score.potential_721_candidate if score else False,
        "estimated_tax_deferral": score.estimated_tax_deferral if score else 0,
        "why_now": why_now_for_property(prop, score) if score else "",
        "recommended_angle": recommended_angle_for_property(prop, score) if score else "",
        "score_breakdown": score_breakdown(score) if score else [],
    }


def query_properties(db: Session) -> list[Property]:
    stmt = (
        select(Property)
        .options(joinedload(Property.score), joinedload(Property.pipeline))
        .join(OpportunityScore)
        .where(Property.units >= 50)
        .order_by(OpportunityScore.call_score.desc(), OpportunityScore.acquisition_score.desc())
    )
    return list(db.scalars(stmt).all())


def passes_intrust_mode(prop: Property) -> bool:
    score = prop.score
    if not score:
        return False
    if prop.units < 75:
        return False
    if not 1970 <= prop.year_built <= 2015:
        return False
    if score.hold_period <= 10:
        return False
    if is_institutional_owner(prop.owner_name) or not is_private_owner(prop.owner_name):
        return False
    if (prop.owner_state or "").upper() not in INTRUST_MODE_OWNER_STATES:
        return False
    return True


def filter_properties(
    properties: list[Property],
    q: str | None = None,
    stage: str | None = None,
    min_score: float | None = None,
    intrust_mode: bool = False,
    recommendation: str | None = None,
) -> list[Property]:
    rows = properties
    if intrust_mode:
        rows = [prop for prop in rows if passes_intrust_mode(prop)]
    if q:
        needle = q.lower()
        rows = [
            prop
            for prop in rows
            if needle in prop.name.lower()
            or needle in prop.owner_name.lower()
            or needle in prop.address.lower()
            or needle in prop.parcel_id.lower()
        ]
    if stage:
        rows = [prop for prop in rows if prop.pipeline and prop.pipeline.stage == stage]
    if min_score is not None:
        rows = [prop for prop in rows if prop.score and prop.score.call_score >= min_score]
    if recommendation:
        rows = [prop for prop in rows if prop.score and prop.score.recommendation == recommendation]
    return rows


def get_ranked_properties(
    db: Session,
    q: str | None = None,
    stage: str | None = None,
    min_score: float | None = None,
    intrust_mode: bool = False,
    recommendation: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    props = filter_properties(
        query_properties(db),
        q=q,
        stage=stage,
        min_score=min_score,
        intrust_mode=intrust_mode,
        recommendation=recommendation,
    )
    payload = [property_to_dict(prop) for prop in props]
    return payload[:limit] if limit else payload


def owner_why_now(owner: dict[str, Any]) -> str:
    reasons: list[str] = []
    if owner["average_hold_period"] >= 15:
        reasons.append(f"Average hold {owner['average_hold_period']:.0f} years")
    if owner["owner_state"] and owner["owner_state"] != "AZ":
        reasons.append(f"{owner['owner_state']} owner")
    if owner["potential_721_candidate"]:
        reasons.append("potential 721 candidate")
    if owner["average_rent_gap"] >= 18:
        reasons.append("below-market rents")
    if owner["estimated_tax_deferral"] > 0:
        reasons.append(f"estimated {money(owner['estimated_tax_deferral'])} tax deferral opportunity")
    if not reasons:
        reasons.append("watch for new ownership motivation signals")
    return ". ".join(reasons[:5]) + "."


def owner_angle(owner: dict[str, Any]) -> str:
    if owner["potential_721_candidate"]:
        return "Open with 721 exchange optionality, embedded gain, and a quiet tax-efficient exit path."
    if owner["owner_state"] and owner["owner_state"] != "AZ":
        return "Open with local Tucson execution and a confidential valuation conversation."
    if owner["average_hold_period"] >= 20:
        return "Open around legacy ownership, succession planning, and certainty of close."
    return "Open with a low-pressure portfolio review and off-market pricing feedback."


def get_owner_profiles(db: Session, intrust_mode: bool = False, limit: int | None = None) -> list[dict[str, Any]]:
    props = filter_properties(query_properties(db), intrust_mode=intrust_mode)
    grouped: dict[str, list[Property]] = defaultdict(list)
    for prop in props:
        grouped[prop.owner_name].append(prop)

    owners: list[dict[str, Any]] = []
    for owner_name, owned in grouped.items():
        scores = [prop.score for prop in owned if prop.score]
        if not scores:
            continue
        owner_state = owned[0].owner_state
        total_units = sum(prop.units for prop in owned)
        portfolio_value = sum(max(prop.assessed_value, prop.assessed_value / max(1 - score.basis_gap / 100, 0.45)) for prop, score in zip(owned, scores))
        avg_hold = mean(score.hold_period for score in scores)
        avg_fit = mean(score.fit_score for score in scores)
        avg_motivation = mean(score.motivation_score for score in scores)
        avg_call = mean(score.call_score for score in scores)
        top_asset = max(owned, key=lambda prop: prop.score.call_score if prop.score else 0)
        potential_721 = any(score.potential_721_candidate for score in scores)
        estimated_tax_deferral = sum(score.estimated_tax_deferral for score in scores)
        average_rent_gap = mean(score.rent_gap for score in scores)
        oldest = min(prop.last_sale_year for prop in owned)
        newest = max(prop.last_sale_year for prop in owned)
        profile = {
            "owner": owner_name,
            "mailing_address": owned[0].mailing_address,
            "owner_city": owned[0].owner_city,
            "owner_state": owner_state,
            "properties_owned": len(owned),
            "units_owned": total_units,
            "estimated_portfolio_value": round(portfolio_value, 0),
            "average_hold_period": round(avg_hold, 1),
            "oldest_acquisition": oldest,
            "newest_acquisition": newest,
            "average_rent_gap": round(average_rent_gap, 1),
            "acquisition_score": round(mean(score.acquisition_score for score in scores), 1),
            "fit_score": round(avg_fit, 1),
            "motivation_score": round(avg_motivation, 1),
            "call_score": round(avg_call, 1),
            "outreach_score": round(avg_motivation, 1),
            "potential_721_candidate": potential_721,
            "estimated_tax_deferral": estimated_tax_deferral,
            "recommendation": (
                "Call Owner"
                if (avg_call >= 88.5 and avg_fit >= 86 and avg_motivation >= 87) or (potential_721 and avg_call >= 90)
                else "Monitor"
                if avg_call >= 58
                else "Ignore"
            ),
            "top_property": property_to_dict(top_asset),
            "properties": [property_to_dict(prop) for prop in sorted(owned, key=lambda p: p.score.call_score if p.score else 0, reverse=True)],
        }
        profile["why_now"] = owner_why_now(profile)
        profile["recommended_angle"] = owner_angle(profile)
        owners.append(profile)

    owners.sort(key=lambda row: (row["call_score"], row["motivation_score"], row["units_owned"]), reverse=True)
    ranked = []
    for index, row in enumerate(owners, start=1):
        ranked.append({"rank": index, **row})
    return ranked[:limit] if limit else ranked


def get_owner_profile(db: Session, owner_name: str) -> dict[str, Any] | None:
    for owner in get_owner_profiles(db, intrust_mode=False):
        if owner["owner"].lower() == owner_name.lower():
            return owner
    return None


def get_market_summary(db: Session) -> dict[str, Any]:
    props = query_properties(db)
    owners = get_owner_profiles(db)
    scores = [prop.score for prop in props if prop.score]
    pipeline_rows = list(db.scalars(select(Pipeline)).all())
    stage_counts = {stage: 0 for stage in PIPELINE_STAGES}
    for row in pipeline_rows:
        stage_counts[row.stage] = stage_counts.get(row.stage, 0) + 1

    source_counts: dict[str, int] = {}
    for prop in props:
        source_counts[prop.source] = source_counts.get(prop.source, 0) + 1
    fallback_records = sum(count for source, count in source_counts.items() if "Seeded" in source)
    live_records = len(props) - fallback_records

    call_owner = [score for score in scores if score.recommendation == "Call Owner"]
    long_hold_owner_names = {
        prop.owner_name
        for prop in props
        if prop.score and prop.score.hold_period >= 15
    }
    return {
        "market": "Tucson, Arizona",
        "total_properties": len(props),
        "total_owners": len(owners),
        "high_score_targets": len(call_owner),
        "long_hold_owners": len(long_hold_owner_names),
        "average_hold_period": round(mean(score.hold_period for score in scores), 1) if scores else 0,
        "average_rent_gap": round(mean(score.rent_gap for score in scores), 1) if scores else 0,
        "average_call_score": round(mean(score.call_score for score in scores), 1) if scores else 0,
        "potential_721_candidates": sum(1 for score in scores if score.potential_721_candidate),
        "data_provenance": {
            "mode": "Seeded fallback" if live_records == 0 else "Live public data + fallback",
            "live_records": live_records,
            "fallback_records": fallback_records,
            "source_counts": source_counts,
            "disclaimer": (
                "Seeded fallback records are pilot/demo intelligence and are not verified real acquisition opportunities."
                if fallback_records
                else "Records are sourced from public data attempts and still require analyst verification before outreach."
            ),
        },
        "reporting": {
            "owners_researched": stage_counts.get("Research", 0)
            + stage_counts.get("Contacted", 0)
            + stage_counts.get("Meeting", 0)
            + stage_counts.get("LOI", 0)
            + stage_counts.get("Closed", 0),
            "owners_contacted": stage_counts.get("Contacted", 0)
            + stage_counts.get("Meeting", 0)
            + stage_counts.get("LOI", 0)
            + stage_counts.get("Closed", 0),
            "meetings_generated": stage_counts.get("Meeting", 0) + stage_counts.get("LOI", 0) + stage_counts.get("Closed", 0),
            "off_market_opportunities": stage_counts.get("Meeting", 0) + stage_counts.get("LOI", 0),
            "lois_submitted": stage_counts.get("LOI", 0) + stage_counts.get("Closed", 0),
            "deals_closed": stage_counts.get("Closed", 0),
        },
        "pipeline": stage_counts,
    }


def get_today_call_list(db: Session) -> dict[str, Any]:
    top_owners = get_owner_profiles(db, intrust_mode=True, limit=25)
    if len(top_owners) < 10:
        top_owners = get_owner_profiles(db, intrust_mode=False, limit=25)
    top_properties = get_ranked_properties(db, intrust_mode=True, limit=25)
    if len(top_properties) < 10:
        top_properties = get_ranked_properties(db, intrust_mode=False, limit=25)
    new_opportunities = [
        prop
        for prop in get_ranked_properties(db, recommendation="Call Owner", limit=25)
        if prop["stage"] in {"Identified", "Research"}
    ][:10]
    return {
        "top_10_owners": top_owners[:10],
        "top_25_owners": top_owners[:25],
        "top_25_properties": top_properties[:25],
        "top_new_opportunities": new_opportunities,
    }
