"""Real Universe importer.

Accepts a manual CSV/XLSX export (HelloData / Yardi / RealPage / analyst research),
normalizes the columns, attempts a Pima County parcel match, and upserts the records
as ``live_authorized`` data with a parcel-match confidence status.

Per the pilot's data-integrity rule, imported records are never auto-promoted to the
real call list. A Pima match lands a record in ``needs_review`` for an analyst to
confirm (-> ``verified``) or reject. Records with no parcel match land in ``no_match``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Property
from backend.app.services.scanner import _lookup_pima_by_address
from backend.app.services.seed_data import upsert_property

try:  # chardet ships with the project; degrade gracefully if absent.
    import chardet
except Exception:  # noqa: BLE001
    chardet = None  # type: ignore[assignment]


# Canonical field -> accepted header variants (compared after normalization).
COLUMN_ALIASES: dict[str, list[str]] = {
    "name": ["propertyname", "property", "name", "community", "communityname", "apartmentname", "buildingname", "asset", "assetname"],
    "address": ["address", "propertyaddress", "siteaddress", "streetaddress", "location", "fulladdress", "addr"],
    "units": ["units", "unitcount", "units", "nounits", "noofunits", "totalunits", "numberofunits", "unit", "doors"],
    "year_built": ["yearbuilt", "built", "yrbuilt", "vintage", "yearbuiltoriginal", "constructionyear"],
    "average_rent": ["averagerent", "avgrent", "currentrent", "inplacerent", "rent", "effectiverent", "actualrent"],
    "market_rent": ["marketrent", "proformarent", "achievablerent", "askingrent", "targetrent"],
    "owner_name": ["owner", "ownername", "ownership", "ownershipentity", "trueowner"],
    "owner_city": ["ownercity", "mailingcity", "city"],
    "owner_state": ["ownerstate", "mailingstate", "state", "st"],
    "last_sale_year": ["lastsaleyear", "yearpurchased", "saleyear", "acquired", "acquisitionyear", "purchaseyear"],
    "source": ["source", "datasource", "provider"],
}

REQUIRED_ANY = ["address", "name"]  # need at least one identifier
DEFAULT_LAST_SALE_YEAR = 2012  # neutral placeholder when an import omits sale year


def _normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (header or "").strip().lower())


def _build_column_map(headers: list[str]) -> dict[str, str]:
    """Map canonical field -> actual header string present in the file."""
    normalized = {_normalize_header(h): h for h in headers if h}
    mapping: dict[str, str] = {}
    for canonical, variants in COLUMN_ALIASES.items():
        for variant in variants:
            if variant in normalized:
                mapping[canonical] = normalized[variant]
                break
    return mapping


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    match = re.search(r"-?\d[\d,]*", str(value))
    if not match:
        return 0
    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return 0


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    match = re.search(r"-?\d[\d,]*\.?\d*", str(value))
    if not match:
        return 0.0
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return 0.0


def _decode_csv(content: bytes) -> str:
    if chardet is not None:
        guess = chardet.detect(content) or {}
        encoding = guess.get("encoding") or "utf-8"
    else:
        encoding = "utf-8"
    try:
        return content.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return content.decode("utf-8", errors="replace")


def parse_rows(filename: str, content: bytes) -> list[dict[str, str]]:
    """Return a list of {header: value} dicts from a CSV or XLSX upload."""
    lower = (filename or "").lower()
    if lower.endswith((".xlsx", ".xlsm")):
        return _parse_xlsx(content)
    if lower.endswith(".xls"):
        raise ValueError("Legacy .xls is not supported. Re-save as .xlsx or .csv and re-upload.")
    return _parse_csv(content)


def _parse_csv(content: bytes) -> list[dict[str, str]]:
    text = _decode_csv(content)
    text = text.lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, str]] = []
    for raw in reader:
        rows.append({(k or "").strip(): ("" if v is None else str(v).strip()) for k, v in raw.items()})
    return rows


def _parse_xlsx(content: bytes) -> list[dict[str, str]]:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheet = workbook.active
    rows_iter = sheet.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        return []
    headers = [("" if cell is None else str(cell).strip()) for cell in header_row]
    rows: list[dict[str, str]] = []
    for values in rows_iter:
        if values is None or all(cell is None or str(cell).strip() == "" for cell in values):
            continue
        record: dict[str, str] = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            cell = values[idx] if idx < len(values) else None
            record[header] = "" if cell is None else str(cell).strip()
        rows.append(record)
    workbook.close()
    return rows


def normalize_address(address: str) -> str:
    clean = re.sub(r"\s+", " ", (address or "").strip())
    clean = clean.strip(", ")
    if not clean:
        return ""
    # Ensure city/state context for Tucson parcel matching when the export omits it.
    upper = clean.upper()
    if "AZ" not in upper and "ARIZONA" not in upper:
        if "TUCSON" not in upper:
            clean = f"{clean}, Tucson, AZ"
        else:
            clean = f"{clean}, AZ"
    return clean


def _street_tokens(address: str) -> list[str]:
    head = (address or "").split(",")[0].upper()
    return [t for t in re.split(r"\s+", head) if t]


def _match_confidence(input_address: str, matched_address: str) -> float:
    a = _street_tokens(input_address)
    b = _street_tokens(matched_address)
    if not a or not b:
        return 0.0
    confidence = 0.0
    # Street number agreement is the strongest single signal.
    if a[0].isdigit() and b and a[0] == b[0]:
        confidence += 0.5
    a_rest = set(a[1:])
    b_rest = set(b[1:])
    if a_rest:
        overlap = len(a_rest & b_rest) / len(a_rest)
        confidence += 0.5 * overlap
    return round(min(confidence, 1.0), 2)


def _synthetic_parcel_id(address: str, name: str) -> str:
    seed = (normalize_address(address) or name or "unknown").upper()
    return f"IMP-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12].upper()}"


def import_universe(
    db: Session,
    filename: str,
    content: bytes,
    source_name: str = "",
    auto_verify_threshold: float = 0.9,
) -> dict[str, Any]:
    """Parse, match, and upsert an export. Returns a structured summary."""
    rows = parse_rows(filename, content)
    if not rows:
        return {
            "status": "error",
            "error": "No rows found in the uploaded file.",
            "rows_seen": 0,
            "imported": 0,
        }

    headers = list(rows[0].keys())
    column_map = _build_column_map(headers)
    if not any(field in column_map for field in REQUIRED_ANY):
        return {
            "status": "error",
            "error": "Could not find a property name or address column. Provide at least one.",
            "rows_seen": len(rows),
            "imported": 0,
            "detected_columns": headers,
        }
    if "units" not in column_map:
        return {
            "status": "error",
            "error": "Could not find a units / unit count column. It is required.",
            "rows_seen": len(rows),
            "imported": 0,
            "detected_columns": headers,
        }

    source_label = source_name.strip() or "Manual import"
    summary = {
        "status": "ok",
        "filename": filename,
        "source_name": source_label,
        "rows_seen": len(rows),
        "imported": 0,
        "needs_review": 0,
        "verified": 0,
        "no_match": 0,
        "skipped": 0,
        "skipped_reasons": [],
        "column_map": column_map,
        "sample": [],
    }

    def get(row: dict[str, str], field: str) -> str:
        header = column_map.get(field)
        return row.get(header, "") if header else ""

    for index, row in enumerate(rows):
        name = get(row, "name").strip()
        address = normalize_address(get(row, "address"))
        units = _to_int(get(row, "units"))

        if not name and not address:
            summary["skipped"] += 1
            continue
        if units <= 0:
            summary["skipped"] += 1
            if len(summary["skipped_reasons"]) < 8:
                summary["skipped_reasons"].append(f"Row {index + 2}: missing/invalid units ({name or address})")
            continue

        pima = _lookup_pima_by_address(address) if address else None
        if pima and pima.get("parcel_id"):
            matched_address = ""  # Pima lookup returns owner/parcel; site address not echoed
            confidence = 0.6  # a successful fuzzy parcel hit, pending analyst confirmation
            if confidence >= auto_verify_threshold:
                match_status = "verified"
            else:
                match_status = "needs_review"
            parcel_id = pima["parcel_id"]
        else:
            confidence = 0.0
            match_status = "no_match"
            parcel_id = _synthetic_parcel_id(address, name)
            pima = pima or {}

        year_built = _to_int(get(row, "year_built")) or int(_to_float(pima.get("year_built", 0))) or 1985
        last_sale_year = _to_int(get(row, "last_sale_year")) or DEFAULT_LAST_SALE_YEAR
        average_rent = _to_float(get(row, "average_rent"))
        market_rent = _to_float(get(row, "market_rent"))
        if market_rent and not average_rent:
            average_rent = round(market_rent * 0.82, 0)
        assessed_value = _to_float(pima.get("assessed_value", 0)) or units * 95_000
        row_source = get(row, "source").strip()

        payload = {
            "parcel_id": parcel_id,
            "name": name or address.split(",")[0],
            "address": address or f"{name}, Tucson, AZ",
            "units": units,
            "year_built": year_built,
            "building_sqft": int(units * 875),
            "assessed_value": assessed_value,
            "owner_name": get(row, "owner_name").strip() or pima.get("owner_name") or "Owner pending parcel match",
            "mailing_address": pima.get("mailing_address") or "Mailing address pending parcel match",
            "latitude": pima.get("latitude") or 32.2226,
            "longitude": pima.get("longitude") or -110.9747,
            "property_type": "Apartments",
            "submarket": "Tucson",
            "owner_city": get(row, "owner_city").strip() or pima.get("owner_city") or "",
            "owner_state": (get(row, "owner_state").strip() or pima.get("owner_state") or "").upper(),
            "source": f"{source_label}: {row_source}" if row_source else source_label,
            "source_name": source_label,
            "source_url": "",
            "last_sale_year": last_sale_year,
            "average_rent": average_rent,
            "market_rent": market_rent,
            "data_status": "live_authorized",
            "match_status": match_status,
            "match_confidence": confidence,
            "matched_address": matched_address if match_status != "no_match" else "",
            "last_verified_at": datetime.utcnow() if match_status == "verified" else None,
        }
        upsert_property(db, payload)

        summary["imported"] += 1
        summary[match_status if match_status in {"needs_review", "verified", "no_match"} else "needs_review"] += 1
        if len(summary["sample"]) < 8:
            summary["sample"].append(
                {
                    "name": payload["name"],
                    "address": payload["address"],
                    "units": units,
                    "match_status": match_status,
                    "parcel_id": parcel_id,
                }
            )

    db.commit()
    return summary
