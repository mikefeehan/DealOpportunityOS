"""Parcel-match review queue.

Imported records land in ``needs_review`` (a Pima parcel hit, unconfirmed) or
``no_match`` (no parcel found). An analyst confirms a match (-> ``verified``,
which lets the record enter the real call list) or rejects the record (removed).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.models import Property

REVIEW_STATUSES = ("needs_review", "no_match")
_STATUS_ORDER = {"needs_review": 0, "no_match": 1, "verified": 2}


def _review_row(prop: Property) -> dict[str, Any]:
    score = prop.score
    return {
        "id": prop.id,
        "parcel_id": prop.parcel_id,
        "name": prop.name,
        "address": prop.address,
        "units": prop.units,
        "year_built": prop.year_built,
        "owner_name": prop.owner_name,
        "owner_state": prop.owner_state,
        "mailing_address": prop.mailing_address,
        "source": prop.source,
        "source_name": prop.source_name,
        "data_status": prop.data_status,
        "match_status": prop.match_status,
        "match_confidence": prop.match_confidence,
        "matched_address": prop.matched_address,
        "call_score": score.call_score if score else 0,
        "recommendation": score.recommendation if score else "Monitor",
        "last_verified_at": prop.last_verified_at.isoformat() + "Z" if prop.last_verified_at else None,
    }


def get_review_queue(db: Session, include_verified: bool = False) -> dict[str, Any]:
    statuses = list(REVIEW_STATUSES) + (["verified"] if include_verified else [])
    stmt = (
        select(Property)
        .options(joinedload(Property.score))
        .where(Property.data_status != "seeded_fallback")
        .where(Property.match_status.in_(statuses))
    )
    rows = list(db.scalars(stmt).all())
    rows.sort(
        key=lambda p: (
            _STATUS_ORDER.get(p.match_status, 9),
            -(p.match_confidence or 0),
            -(p.units or 0),
        )
    )
    queue = [_review_row(prop) for prop in rows]
    return {
        "total": len(queue),
        "needs_review": sum(1 for r in queue if r["match_status"] == "needs_review"),
        "no_match": sum(1 for r in queue if r["match_status"] == "no_match"),
        "verified": sum(1 for r in queue if r["match_status"] == "verified"),
        "records": queue,
    }


def confirm_match(db: Session, property_id: int) -> dict[str, Any] | None:
    prop = db.get(Property, property_id)
    if not prop:
        return None
    prop.match_status = "verified"
    prop.last_verified_at = datetime.utcnow()
    if (prop.match_confidence or 0) < 1:
        prop.match_confidence = 1.0
    db.commit()
    db.refresh(prop)
    return {"id": prop.id, "match_status": prop.match_status, "last_verified_at": prop.last_verified_at.isoformat() + "Z"}


def reject_record(db: Session, property_id: int) -> dict[str, Any] | None:
    prop = db.get(Property, property_id)
    if not prop:
        return None
    if prop.data_status == "seeded_fallback":
        return {"id": property_id, "status": "skipped", "reason": "Seeded fallback records cannot be rejected here."}
    db.delete(prop)
    db.commit()
    return {"id": property_id, "status": "rejected"}
