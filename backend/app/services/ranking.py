from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models import OpportunityScore, Pipeline, Property
from backend.app.services.scoring import (
    INTRUST_MODE_OWNER_STATES,
    PIPELINE_STAGES,
    estimate_dscr,
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
        "avg_unit_sf": prop.avg_unit_sf,
        "assessed_value": prop.assessed_value,
        "owner_name": prop.owner_name,
        "mailing_address": prop.mailing_address,
        "owner_city": prop.owner_city,
        "owner_state": prop.owner_state,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "property_type": prop.property_type,
        "submarket": prop.submarket,
        "market": prop.market,
        "sources": prop.sources,
        "star_rating": prop.star_rating,
        "building_class": prop.building_class,
        "location_rating": prop.location_rating,
        "cap_rate": prop.cap_rate,
        "vacancy": prop.vacancy,
        "for_sale": prop.for_sale,
        "for_sale_price": prop.for_sale_price,
        "price_per_unit": prop.price_per_unit,
        "last_sale_price": prop.last_sale_price,
        "affordable": prop.affordable,
        "affordable_type": prop.affordable_type,
        "loan_maturity_year": prop.loan_maturity_year,
        "interest_rate": prop.interest_rate,
        "loan_amount": prop.loan_amount,
        "dscr": estimate_dscr(prop),
        "year_renovated": prop.year_renovated,
        "effective_rent": prop.effective_rent,
        "owner_contact": prop.owner_contact,
        "owner_phone": prop.owner_phone,
        "owner_email": prop.owner_email,
        "owner_website": prop.owner_website,
        "manager_phone": prop.manager_phone,
        "source": prop.source,
        "source_name": prop.source_name,
        "source_url": prop.source_url,
        "data_status": prop.data_status,
        "match_status": prop.match_status,
        "match_confidence": prop.match_confidence,
        "matched_address": prop.matched_address,
        "last_verified_at": prop.last_verified_at.isoformat() + "Z" if prop.last_verified_at else None,
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


def has_verified_live(db: Session) -> bool:
    stmt = (
        select(Property.id)
        .where(Property.match_status == "verified", Property.data_status != "seeded_fallback")
        .limit(1)
    )
    return db.scalar(stmt) is not None


def has_live(db: Session) -> bool:
    stmt = select(Property.id).where(Property.data_status != "seeded_fallback").limit(1)
    return db.scalar(stmt) is not None


def resolve_scope(db: Session, data_scope: str | None) -> str | None:
    """Translate a requested scope into a property filter.

    - "verified": parcel-verified live records only.
    - "live": any imported live record (verified or not), hides demo fallback.
    - "all": everything (includes seeded demo fallback).
    - "auto"/None: verified-live if any exist, else any live, else everything
      so the dashboard always loads.
    """
    scope = (data_scope or "auto").lower()
    if scope in {"verified", "live"}:
        return scope
    if scope == "all":
        return None
    if has_verified_live(db):
        return "verified"
    if has_live(db):
        return "live"
    return None


def query_properties(db: Session, scope: str | None = None, market: str | None = None) -> list[Property]:
    stmt = (
        select(Property)
        .options(joinedload(Property.score), joinedload(Property.pipeline))
        .join(OpportunityScore)
        .where(Property.units >= 50)
        .where(Property.property_type != "Under Construction")
        .order_by(OpportunityScore.call_score.desc(), OpportunityScore.acquisition_score.desc())
    )
    if scope == "verified":
        stmt = stmt.where(Property.match_status == "verified", Property.data_status != "seeded_fallback")
    elif scope == "live":
        stmt = stmt.where(Property.data_status != "seeded_fallback")
    if market:
        stmt = stmt.where(Property.market == market)
    return list(db.scalars(stmt).all())


def list_markets(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(Property.market, func.count(Property.id))
        .where(Property.data_status != "seeded_fallback")
        .where(Property.units >= 50)
        .group_by(Property.market)
        .order_by(func.count(Property.id).desc())
    )
    return [{"market": market or "Unknown", "properties": count} for market, count in db.execute(stmt).all()]


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
    # Owner location is intentionally NOT a filter — we don't care where the
    # owner lives, only the asset, hold, and ownership profile.
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
    data_scope: str | None = None,
    market: str | None = None,
) -> list[dict[str, Any]]:
    scope = resolve_scope(db, data_scope)
    props = filter_properties(
        query_properties(db, scope=scope, market=market),
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


def get_owner_profiles(
    db: Session,
    intrust_mode: bool = False,
    limit: int | None = None,
    data_scope: str | None = None,
    market: str | None = None,
) -> list[dict[str, Any]]:
    scope = resolve_scope(db, data_scope)
    props = filter_properties(query_properties(db, scope=scope, market=market), intrust_mode=intrust_mode)
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
        owner_data_status = (
            "seeded_fallback"
            if all((prop.data_status or "seeded_fallback") == "seeded_fallback" for prop in owned)
            else "live"
        )
        def first_nonempty(attr: str) -> str:
            for prop in owned:
                value = getattr(prop, attr, "") or ""
                if value:
                    return value
            return ""

        profile = {
            "owner": owner_name,
            "data_status": owner_data_status,
            "mailing_address": owned[0].mailing_address,
            "owner_contact": first_nonempty("owner_contact"),
            "owner_phone": first_nonempty("owner_phone"),
            "owner_email": first_nonempty("owner_email"),
            "owner_website": first_nonempty("owner_website"),
            "manager_phone": first_nonempty("manager_phone"),
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
                if (avg_call >= 78 and avg_motivation >= 84) or (potential_721 and avg_call >= 80)
                else "Monitor"
                if avg_call >= 55
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
    # Detail/call-prep lookups must resolve any owner, including demo fallback.
    for owner in get_owner_profiles(db, intrust_mode=False, data_scope="all"):
        if owner["owner"].lower() == owner_name.lower():
            return owner
    return None


def get_map_points(db: Session, data_scope: str | None = None, market: str | None = None) -> list[dict[str, Any]]:
    """Lightweight geo payload for the map: only sites with real coordinates."""
    scope = resolve_scope(db, data_scope)
    points: list[dict[str, Any]] = []
    for prop in query_properties(db, scope=scope, market=market):
        if abs(prop.latitude or 0) < 0.1 or abs(prop.longitude or 0) < 0.1:
            continue
        score = prop.score
        points.append(
            {
                "id": prop.id,
                "name": prop.name,
                "address": prop.address,
                "owner_name": prop.owner_name,
                "lat": prop.latitude,
                "lon": prop.longitude,
                "units": prop.units,
                "year_built": prop.year_built,
                "submarket": prop.submarket,
                "market": prop.market,
                "star_rating": prop.star_rating,
                "building_class": prop.building_class,
                "affordable": prop.affordable,
                "for_sale": prop.for_sale,
                "call_score": score.call_score if score else 0,
                "recommendation": score.recommendation if score else "Monitor",
                "rent_gap": score.rent_gap if score else 0,
                "hold_period": score.hold_period if score else 0,
                "potential_721_candidate": score.potential_721_candidate if score else False,
            }
        )
    return points


def get_market_summary(db: Session, market: str | None = None) -> dict[str, Any]:
    props = query_properties(db, market=market)
    owners = get_owner_profiles(db, market=market)
    scores = [prop.score for prop in props if prop.score]
    pipeline_rows = list(db.scalars(select(Pipeline)).all())
    stage_counts = {stage: 0 for stage in PIPELINE_STAGES}
    for row in pipeline_rows:
        stage_counts[row.stage] = stage_counts.get(row.stage, 0) + 1

    source_counts: dict[str, int] = {}
    for prop in props:
        source_counts[prop.source] = source_counts.get(prop.source, 0) + 1

    all_props = list(db.scalars(select(Property)).all())
    fallback_records = sum(1 for prop in all_props if prop.data_status == "seeded_fallback")
    live_records = sum(1 for prop in all_props if prop.data_status != "seeded_fallback")
    verified_live_records = sum(
        1 for prop in all_props if prop.match_status == "verified" and prop.data_status != "seeded_fallback"
    )
    needs_review_records = sum(
        1 for prop in all_props if prop.match_status in {"needs_review", "no_match"} and prop.data_status != "seeded_fallback"
    )

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
            "mode": (
                "Verified live"
                if verified_live_records > 0 and fallback_records == 0
                else "Verified live + fallback"
                if verified_live_records > 0
                else "Seeded fallback"
                if live_records == 0
                else "Imported, pending review"
            ),
            "live_records": live_records,
            "verified_live_records": verified_live_records,
            "needs_review_records": needs_review_records,
            "fallback_records": fallback_records,
            "source_counts": source_counts,
            "disclaimer": (
                "Seeded fallback records are pilot/demo intelligence and are not verified real acquisition opportunities."
                if fallback_records and verified_live_records == 0
                else "Imported records require analyst parcel-match confirmation before entering the real call list."
                if needs_review_records and verified_live_records == 0
                else "Records are analyst-verified against Pima County parcel data."
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


def get_today_call_list(db: Session, data_scope: str | None = None, market: str | None = None) -> dict[str, Any]:
    top_owners = get_owner_profiles(db, intrust_mode=True, limit=25, data_scope=data_scope, market=market)
    if len(top_owners) < 10:
        top_owners = get_owner_profiles(db, intrust_mode=False, limit=25, data_scope=data_scope, market=market)
    top_properties = get_ranked_properties(db, intrust_mode=True, limit=25, data_scope=data_scope, market=market)
    if len(top_properties) < 10:
        top_properties = get_ranked_properties(db, intrust_mode=False, limit=25, data_scope=data_scope, market=market)
    new_opportunities = [
        prop
        for prop in get_ranked_properties(db, recommendation="Call Owner", limit=25, data_scope=data_scope, market=market)
        if prop["stage"] in {"Identified", "Research"}
    ][:10]
    return {
        "top_10_owners": top_owners[:10],
        "top_25_owners": top_owners[:25],
        "top_25_properties": top_properties[:25],
        "top_new_opportunities": new_opportunities,
    }
