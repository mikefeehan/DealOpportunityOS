"""Mapbox geocoding for sites that arrive without coordinates (e.g. CoStar).

Reads the Mapbox token from MAPBOX_TOKEN, falling back to the frontend's
NEXT_PUBLIC_MAPBOX_TOKEN in .env.local so it works in local dev without extra
env plumbing. Geocodes properties whose latitude/longitude are missing so they
appear on the map.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Property

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_LOCAL = ROOT_DIR / "frontend" / ".env.local"
GEOCODE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"


def get_mapbox_token() -> str:
    token = os.getenv("MAPBOX_TOKEN", "").strip()
    if token:
        return token
    if ENV_LOCAL.exists():
        for line in ENV_LOCAL.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.match(r"\s*(?:NEXT_PUBLIC_)?MAPBOX_TOKEN\s*=\s*(.+)\s*$", line)
            if match:
                return match.group(1).strip().strip('"').strip("'")
    return ""


def _missing_coords(prop: Property) -> bool:
    return abs(prop.latitude or 0) < 0.1 or abs(prop.longitude or 0) < 0.1


def _market_centroid(db: Session, market: str | None) -> tuple[float, float]:
    stmt = select(Property.latitude, Property.longitude).where(
        Property.data_status != "seeded_fallback"
    )
    if market:
        stmt = stmt.where(Property.market == market)
    lats, lons = [], []
    for lat, lon in db.execute(stmt).all():
        if abs(lat or 0) > 0.1 and abs(lon or 0) > 0.1:
            lats.append(lat)
            lons.append(lon)
    if lats:
        return sum(lons) / len(lons), sum(lats) / len(lats)
    return -110.95, 32.2  # Tucson fallback


def geocode_address(address: str, token: str, proximity: tuple[float, float]) -> tuple[float, float] | None:
    if not address:
        return None
    url = GEOCODE_URL.format(query=quote(address))
    params = {
        "access_token": token,
        "limit": 1,
        "country": "us",
        "types": "address",
        "proximity": f"{proximity[0]},{proximity[1]}",
    }
    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        features = response.json().get("features", [])
    except Exception:  # noqa: BLE001 - skip a failed address, keep going
        return None
    if not features:
        return None
    center = features[0].get("center")
    if not center or len(center) != 2:
        return None
    lon, lat = center
    return float(lat), float(lon)


def geocode_missing(db: Session, market: str | None = None, limit: int = 1000) -> dict[str, Any]:
    token = get_mapbox_token()
    if not token:
        return {"status": "error", "error": "No Mapbox token (set MAPBOX_TOKEN or frontend/.env.local).", "geocoded": 0}

    stmt = select(Property).where(Property.data_status != "seeded_fallback").where(Property.address != "")
    if market:
        stmt = stmt.where(Property.market == market)
    candidates = [prop for prop in db.scalars(stmt).all() if _missing_coords(prop)]
    proximity = _market_centroid(db, market)

    geocoded = 0
    failed = 0
    for prop in candidates[:limit]:
        result = geocode_address(prop.address, token, proximity)
        if result:
            prop.latitude, prop.longitude = result
            geocoded += 1
        else:
            failed += 1
    db.commit()
    return {
        "status": "ok",
        "candidates": len(candidates),
        "geocoded": geocoded,
        "failed": failed,
        "remaining": max(0, len(candidates) - geocoded),
    }
