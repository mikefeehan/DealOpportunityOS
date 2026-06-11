from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.app.models import Property
from backend.app.services.seed_data import ensure_seed_data, upsert_property


LOGGER = logging.getLogger("opportunityos.scan")
if not LOGGER.handlers:
    LOGGER.setLevel(logging.INFO)
    handler = logging.FileHandler("opportunityos_scan.log")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOGGER.addHandler(handler)


PIMA_PROPERTY_LAYER = "https://mapdata.tucsonaz.gov/public/rest/services/PublicMaps/PropertyHousing/MapServer/17/query"
TUCSON_PROPERTY_LAYER = "https://mapdata.tucsonaz.gov/public/rest/services/PublicMaps/PropertyHousing/MapServer/40/query"
ROOT_DIR = Path(__file__).resolve().parents[3]
SOURCE_URLS_FILE = ROOT_DIR / "data" / "source_urls.txt"


PUBLIC_SOURCE_ATTEMPTS = [
    {
        "name": "Pima County GIS parcel layer",
        "type": "arcgis",
        "url": PIMA_PROPERTY_LAYER,
    },
    {
        "name": "Tucson public parcel layer",
        "type": "arcgis",
        "url": TUCSON_PROPERTY_LAYER,
    },
    {
        "name": "Pima County Assessor",
        "type": "healthcheck",
        "url": "https://www.asr.pima.gov/advanced-search",
    },
    {
        "name": "Apartments.com Tucson",
        "type": "rental_market_check",
        "url": "https://www.apartments.com/tucson-az/",
    },
    {
        "name": "Zillow Rentals Tucson",
        "type": "rental_market_check",
        "url": "https://www.zillow.com/tucson-az/rentals/",
    },
    {
        "name": "RentCafe Tucson",
        "type": "rental_market_check",
        "url": "https://www.rentcafe.com/apartments-for-rent/us/az/tucson/",
    },
]


def load_configured_source_urls() -> list[str]:
    urls: list[str] = []
    env_urls = os.getenv("ACQUISITION_SOURCE_URLS") or os.getenv("PUBLIC_APARTMENT_SOURCE_URLS", "")
    urls.extend([item.strip() for item in env_urls.split(",") if item.strip()])
    if SOURCE_URLS_FILE.exists():
        for line in SOURCE_URLS_FILE.read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if clean and not clean.startswith("#"):
                urls.append(clean)
    deduped = []
    seen = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def _headers_for_url(url: str) -> dict[str, str]:
    headers = {"User-Agent": "OpportunityOS Tucson pilot"}
    host = urlparse(url).netloc.lower()
    cookie = ""
    if "yardi" in host:
        cookie = os.getenv("YARDI_COOKIE", "")
    elif "realpage" in host:
        cookie = os.getenv("REALPAGE_COOKIE", "")
    elif "hellodata" in host or "hello-data" in host:
        cookie = os.getenv("HELLODATA_COOKIE", "")
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _extract_first(attrs: dict[str, Any], candidates: list[str], default: Any = None) -> Any:
    for candidate in candidates:
        if candidate in attrs and attrs[candidate] not in {None, ""}:
            return attrs[candidate]
    return default


def _number(value: Any, default: float = 0) -> float:
    if value in {None, ""}:
        return default
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _flatten_json_ld(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows: list[dict[str, Any]] = []
        for item in value:
            rows.extend(_flatten_json_ld(item))
        return rows
    if isinstance(value, dict):
        rows = [value]
        graph = value.get("@graph")
        if graph:
            rows.extend(_flatten_json_ld(graph))
        return rows
    return []


def _address_to_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = [
            value.get("streetAddress"),
            value.get("addressLocality"),
            value.get("addressRegion"),
            value.get("postalCode"),
        ]
        return ", ".join(str(part) for part in parts if part)
    return ""


def _extract_units(text: str) -> int:
    patterns = [
        r"(\d{2,4})\s+(?:apartment\s+)?units\b",
        r"(\d{2,4})\s*-\s*unit\b",
        r"(\d{2,4})\s+unit\s+(?:apartment|multifamily)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            units = int(match.group(1))
            if 10 <= units <= 1500:
                return units
    return 0


def _extract_year_built(text: str) -> int:
    patterns = [
        r"year\s+built\s*[:\-]?\s*(19\d{2}|20\d{2})",
        r"built\s+in\s+(19\d{2}|20\d{2})",
        r"\bbuilt\s*[:\-]\s*(19\d{2}|20\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 1985


def _extract_rent_signal(text: str) -> tuple[float, float]:
    rents = [int(value.replace(",", "")) for value in re.findall(r"\$\s?([789]\d{2}|1,\d{3}|1\d{3}|2,\d{3})", text)]
    rents = [rent for rent in rents if 600 <= rent <= 2600]
    if not rents:
        return 950, 1250
    average_rent = min(rents)
    market_rent = max(rents)
    if market_rent <= average_rent:
        market_rent = round(average_rent * 1.18, 0)
    return float(average_rent), float(market_rent)


def _extract_inventory_record(url: str, html: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    record: dict[str, Any] = {
        "name": title.split("|")[0].split("- Apartments")[0].strip() or urlparse(url).netloc,
        "address": "",
        "units": _extract_units(page_text),
        "year_built": _extract_year_built(page_text),
    }

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(data):
            item_type = item.get("@type", "")
            types = item_type if isinstance(item_type, list) else [item_type]
            if not any(str(value).lower() in {"apartmentcomplex", "apartment", "residence", "localbusiness"} for value in types):
                continue
            record["name"] = item.get("name") or record["name"]
            record["address"] = _address_to_string(item.get("address")) or record["address"]
            geo = item.get("geo") or {}
            if isinstance(geo, dict):
                record["latitude"] = _number(geo.get("latitude"), 32.2226)
                record["longitude"] = _number(geo.get("longitude"), -110.9747)
            unit_value = item.get("numberOfRooms") or item.get("numberOfAccommodationUnits") or item.get("numberOfUnits")
            if unit_value and not record["units"]:
                record["units"] = int(_number(unit_value, 0))

    if not record["address"]:
        address_match = re.search(
            r"(\d{2,6}\s+[A-Za-z0-9 .'-]+,\s*Tucson,\s*AZ\s*\d{5})",
            page_text,
            flags=re.IGNORECASE,
        )
        if address_match:
            record["address"] = address_match.group(1)

    average_rent, market_rent = _extract_rent_signal(page_text)
    record["average_rent"] = average_rent
    record["market_rent"] = market_rent

    if not record["address"] or record["units"] < 50:
        return None
    return record


def _address_search_token(address: str) -> str:
    clean = address.split(",")[0].upper()
    parts = clean.split()
    if len(parts) >= 3:
        return " ".join(parts[:3])
    return clean


def _lookup_pima_by_address(address: str) -> dict[str, Any] | None:
    token = _address_search_token(address).replace("'", "''")
    if not token:
        return None
    params = {
        "where": f"UPPER(SITE_ADDRESS) LIKE UPPER('%{token}%')",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "json",
        "resultRecordCount": 1,
    }
    try:
        response = requests.get(PIMA_PROPERTY_LAYER, params=params, timeout=8)
        response.raise_for_status()
        features = response.json().get("features", [])
    except Exception:  # noqa: BLE001
        LOGGER.exception("Pima address enrichment failed for %s", address)
        return None
    if not features:
        return None
    feature = features[0]
    attrs = feature.get("attributes") or {}
    geometry = feature.get("geometry") or {}
    mailing_parts = [
        str(_extract_first(attrs, [field], "")).strip()
        for field in ["MAIL1", "MAIL2", "MAIL3", "MAIL4", "MAIL5"]
        if _extract_first(attrs, [field], "")
    ]
    owner_state = ""
    owner_city = ""
    if mailing_parts:
        last = mailing_parts[-1].replace(",", " ").split()
        if len(last) >= 2 and len(last[-2]) == 2:
            owner_state = last[-2].upper()
        if len(mailing_parts) >= 2:
            owner_city = mailing_parts[-2].split(",")[0].strip()
    return {
        "parcel_id": str(_extract_first(attrs, ["PARCEL", "Parcel", "APN", "PIN"], "")).strip(),
        "owner_name": str(_extract_first(attrs, ["ADDRESSEE", "OWNER", "OWNER_NAME"], "Unknown Owner")).strip(),
        "mailing_address": ", ".join(mailing_parts) or "Mailing address unavailable",
        "assessed_value": _number(_extract_first(attrs, ["FCV", "FULL_CASH_VALUE", "ASSESSED_VALUE"], 0), 0),
        "year_built": int(_number(_extract_first(attrs, ["YearBuilt", "YEARBUILT", "YR_BUILT"], 0), 0)),
        "latitude": float(geometry.get("y") or 32.2226),
        "longitude": float(geometry.get("x") or -110.9747),
        "owner_city": owner_city,
        "owner_state": owner_state,
    }


def _attempt_inventory_url(url: str, db: Session) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=12, headers=_headers_for_url(url))
        if response.status_code in {401, 403}:
            return {
                "source": url,
                "status": "auth_required",
                "records_seen": 0,
                "records_imported": 0,
                "error": "Private source requires a valid local session cookie or source-specific login adapter.",
            }
        response.raise_for_status()
        record = _extract_inventory_record(url, response.text)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Configured source failed: %s", url)
        return {"source": url, "status": "failed", "records_seen": 0, "records_imported": 0, "error": str(exc)}

    if not record:
        return {
            "source": url,
            "status": "no_qualifying_50_unit_record_found",
            "records_seen": 1,
            "records_imported": 0,
            "error": None,
        }

    pima = _lookup_pima_by_address(record["address"]) or {}
    parcel_id = pima.get("parcel_id") or f"WEB-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12].upper()}"
    assessed_value = pima.get("assessed_value") or record["units"] * 95_000
    year_built = pima.get("year_built") or record["year_built"] or 1985
    domain = urlparse(url).netloc
    payload = {
        "parcel_id": parcel_id,
        "name": record["name"],
        "address": record["address"],
        "units": record["units"],
        "year_built": year_built,
        "building_sqft": int(record["units"] * 875),
        "assessed_value": assessed_value,
        "owner_name": pima.get("owner_name") or "Owner pending parcel match",
        "mailing_address": pima.get("mailing_address") or "Mailing address pending parcel match",
        "latitude": pima.get("latitude") or record.get("latitude") or 32.2226,
        "longitude": pima.get("longitude") or record.get("longitude") or -110.9747,
        "property_type": "Apartments",
        "submarket": "Tucson",
        "owner_city": pima.get("owner_city") or "",
        "owner_state": pima.get("owner_state") or "",
        "source": f"Configured authorized source: {domain}",
        "source_name": f"Authorized source: {domain}",
        "source_url": url,
        "last_sale_year": 2011,
        "average_rent": record["average_rent"],
        "market_rent": record["market_rent"],
        "data_status": "live_authorized",
        "match_status": "needs_review" if pima.get("parcel_id") else "no_match",
        "match_confidence": 0.6 if pima.get("parcel_id") else 0.0,
    }
    upsert_property(db, payload)
    db.commit()
    return {"source": url, "status": "ok", "records_seen": 1, "records_imported": 1, "error": None}


def _attempt_arcgis_source(source: dict[str, str], db: Session) -> dict[str, Any]:
    params = {
        "where": "UPPER(USE_DESC) LIKE '%APART%' OR UPPER(USE_DESC) LIKE '%MULTI%'",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "json",
        "resultRecordCount": 100,
    }
    try:
        response = requests.get(source["url"], params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
        features = payload.get("features", [])
    except Exception as exc:  # noqa: BLE001 - scan must continue on public source failures.
        LOGGER.exception("Source failed: %s", source["name"])
        return {"source": source["name"], "status": "failed", "records_seen": 0, "records_imported": 0, "error": str(exc)}

    imported = 0
    for feature in features:
        attrs = feature.get("attributes") or {}
        geometry = feature.get("geometry") or {}
        parcel_id = str(_extract_first(attrs, ["PARCEL", "Parcel", "APN", "PIN"], "")).strip()
        if not parcel_id:
            continue
        building_sqft = int(_number(_extract_first(attrs, ["BLDGSQFT", "BUILDING_SQFT", "SqFt", "SQFT"], 0), 0))
        inferred_units = int(_number(_extract_first(attrs, ["UNITS", "Units", "NO_UNITS"], 0), 0))
        if not inferred_units and building_sqft >= 42_500:
            inferred_units = max(50, round(building_sqft / 850))
        if inferred_units < 50:
            continue

        year_built = int(_number(_extract_first(attrs, ["YearBuilt", "YEARBUILT", "YR_BUILT"], 1985), 1985))
        assessed_value = _number(_extract_first(attrs, ["FCV", "FULL_CASH_VALUE", "ASSESSED_VALUE"], 0), 0)
        if assessed_value <= 0:
            assessed_value = inferred_units * 95_000
        owner_name = str(_extract_first(attrs, ["ADDRESSEE", "OWNER", "OWNER_NAME"], "Unknown Owner")).strip()
        site_address = str(_extract_first(attrs, ["SITE_ADDRESS", "SITUSADDR", "ADDRESS"], "Tucson, AZ")).strip()
        mailing_parts = [
            str(_extract_first(attrs, [field], "")).strip()
            for field in ["MAIL1", "MAIL2", "MAIL3", "MAIL4", "MAIL5"]
            if _extract_first(attrs, [field], "")
        ]
        mailing_address = ", ".join(mailing_parts) or "Mailing address unavailable"
        owner_state = ""
        for part in mailing_parts:
            tokens = part.replace(",", " ").split()
            if len(tokens) >= 2 and tokens[-2].isalpha() and len(tokens[-2]) == 2:
                owner_state = tokens[-2].upper()
        prop = {
            "parcel_id": parcel_id,
            "name": site_address.title(),
            "address": f"{site_address.title()}, Tucson, AZ",
            "units": inferred_units,
            "year_built": year_built,
            "building_sqft": building_sqft,
            "assessed_value": assessed_value,
            "owner_name": owner_name,
            "mailing_address": mailing_address,
            "latitude": float(geometry.get("y") or _number(_extract_first(attrs, ["LAT", "Latitude"], 32.2226), 32.2226)),
            "longitude": float(geometry.get("x") or _number(_extract_first(attrs, ["LON", "LONG", "Longitude"], -110.9747), -110.9747)),
            "property_type": "Apartments",
            "submarket": "Tucson",
            "owner_city": "",
            "owner_state": owner_state,
            "source": source["name"],
            "source_name": source["name"],
            "last_sale_year": 2011,
            "average_rent": 950,
            "market_rent": 1250,
            "data_status": "live_public",
            "match_status": "needs_review",
            "match_confidence": 0.5,
        }
        upsert_property(db, prop)
        imported += 1

    db.commit()
    return {
        "source": source["name"],
        "status": "ok",
        "records_seen": len(features),
        "records_imported": imported,
        "error": None,
    }


def _attempt_healthcheck(source: dict[str, str]) -> dict[str, Any]:
    try:
        response = requests.get(source["url"], timeout=6, headers={"User-Agent": "OpportunityOS Tucson pilot"})
        response.raise_for_status()
        status = "reachable_no_bulk_free_api" if source["type"] != "rental_market_check" else "reachable_market_reference_only"
        return {"source": source["name"], "status": status, "records_seen": 0, "records_imported": 0, "error": None}
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Source failed: %s", source["name"])
        return {"source": source["name"], "status": "failed", "records_seen": 0, "records_imported": 0, "error": str(exc)}


def run_tucson_scan(db: Session) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    imported_total = 0
    configured_urls = load_configured_source_urls()
    if configured_urls:
        for url in configured_urls:
            result = _attempt_inventory_url(url, db)
            imported_total += result.get("records_imported", 0)
            results.append(result)
    else:
        results.append(
            {
                "source": "Configured Yardi/RealPage/HelloData source URLs",
                "status": "not_configured",
                "records_seen": 0,
                "records_imported": 0,
                "error": "Add authorized URLs to data/source_urls.txt or ACQUISITION_SOURCE_URLS.",
            }
        )
    for source in PUBLIC_SOURCE_ATTEMPTS:
        if source["type"] == "arcgis":
            result = _attempt_arcgis_source(source, db)
        else:
            result = _attempt_healthcheck(source)
        imported_total += result.get("records_imported", 0)
        results.append(result)

    seeded_count = ensure_seed_data(db)
    fallback_active = imported_total == 0
    LOGGER.info("Tucson scan finished. imported=%s fallback=%s seeded=%s", imported_total, fallback_active, seeded_count)
    total_properties = db.query(Property).count()
    return {
        "market": "Tucson, Arizona",
        "completed_at": datetime.utcnow().isoformat() + "Z",
        "live_records_imported": imported_total,
        "seeded_records_loaded": seeded_count,
        "fallback_active": fallback_active,
        "total_properties": total_properties,
        "sources": results,
    }
