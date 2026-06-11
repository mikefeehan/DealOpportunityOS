"""HelloData market-rent reference.

Loads a HelloData market-analysis CSV (real asking rents per property) and exposes
a street-address lookup so the importer can attach a real market rent to each owned
property, replacing modeled benchmarks where a match exists.

Drop one or more HelloData CSV exports in ``data/market_reference/`` (gitignored) or
point ``MARKET_REFERENCE_CSV`` at a file. Expected columns include an address column
and a rent column (e.g. "Address" and "Rent").
"""

from __future__ import annotations

import csv
import os
import re
import statistics
from functools import lru_cache
from pathlib import Path

from backend.app.services.addresses import address_key as street_key

ROOT_DIR = Path(__file__).resolve().parents[3]
MARKET_REF_DIR = ROOT_DIR / "data" / "market_reference"


def _money(value: str) -> float:
    match = re.search(r"[\d,]+(\.\d+)?", value or "")
    return float(match.group(0).replace(",", "")) if match else 0.0


def _find_column(fieldnames: list[str], *candidates: str) -> str | None:
    norm = {re.sub(r"[^a-z0-9]", "", (f or "").lower()): f for f in fieldnames}
    for candidate in candidates:
        if candidate in norm:
            return norm[candidate]
    return None


def _candidate_files() -> list[Path]:
    files: list[Path] = []
    env = os.getenv("MARKET_REFERENCE_CSV")
    if env and Path(env).exists():
        files.append(Path(env))
    if MARKET_REF_DIR.exists():
        files.extend(sorted(MARKET_REF_DIR.glob("*.csv")))
    return files


@lru_cache(maxsize=1)
def load_market_reference() -> dict:
    by_street: dict[str, float] = {}
    rents: list[float] = []
    for path in _candidate_files():
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    continue
                addr_col = _find_column(reader.fieldnames, "address", "propertyaddress", "siteaddress")
                rent_col = _find_column(reader.fieldnames, "rent", "askingrent", "marketrent", "effectiverent")
                if not addr_col or not rent_col:
                    continue
                for row in reader:
                    rent = _money(row.get(rent_col, ""))
                    if rent <= 0:
                        continue
                    key = street_key(row.get(addr_col, ""))
                    if key:
                        by_street[key] = rent
                        rents.append(rent)
        except Exception:  # noqa: BLE001 - a bad reference file must not break imports
            continue
    return {
        "by_street": by_street,
        "median": statistics.median(rents) if rents else 0.0,
        "count": len(by_street),
    }


def market_rent_for(address: str) -> float | None:
    """Real HelloData market rent for an address, or None if no match."""
    ref = load_market_reference()
    return ref["by_street"].get(street_key(address))


def market_rent_benchmark() -> float:
    """Median HelloData rent, used as a real-data fallback benchmark (0 if none loaded)."""
    return load_market_reference()["median"]
