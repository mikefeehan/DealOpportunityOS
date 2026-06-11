"""Canonical street-address key for joining records across data sources.

Different providers format the same address differently — Yardi spells out
"West Broadway Boulevard", CoStar abbreviates "W Broadway Blvd". To aggregate
all sources per site we normalize directionals and suffixes to a stable key
(house number + normalized street name).
"""

from __future__ import annotations

import re

_DIRECTIONALS = {
    "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W",
    "NORTHEAST": "NE", "NORTHWEST": "NW", "SOUTHEAST": "SE", "SOUTHWEST": "SW",
}

_SUFFIXES = {
    "AVENUE": "AVE", "AV": "AVE", "BOULEVARD": "BLVD", "BLV": "BLVD", "STREET": "ST",
    "DRIVE": "DR", "ROAD": "RD", "LANE": "LN", "COURT": "CT", "PLACE": "PL",
    "CIRCLE": "CIR", "TERRACE": "TER", "PARKWAY": "PKWY", "HIGHWAY": "HWY",
    "TRAIL": "TRL", "ROUTE": "RTE", "SQUARE": "SQ",
}

# Trailing tokens to drop when building the key (street type words + variants).
_DROP_SUFFIX = set(_SUFFIXES.values()) | {
    "WAY", "LOOP", "PASS", "PT", "SQ", "ROW", "RUN", "BEND", "PASEO", "VIA",
    "CAMINO", "PLAZA", "PIKE", "PATH", "CROSSING", "WALK",
    "PKY", "PKWY", "EXPY", "EXPWY", "FWY", "TPKE", "CTR", "BLV",
}


_DIRECTIONAL_LETTERS = {"N", "S", "E", "W", "NE", "NW", "SE", "SW"}


def address_key(address: str) -> str:
    """Stable join key: house number + up to two normalized street-name tokens.

    Directionals are dropped because providers disagree on whether to include
    them (CoStar "3750 Via Palomita" vs Yardi "3750 East Via Palomita"), which
    would otherwise create duplicate records for the same site.
    """
    head = (address or "").split(",")[0].upper()
    head = re.sub(r"[^A-Z0-9 ]", " ", head)
    tokens = [t for t in head.split() if t]
    normalized: list[str] = []
    for token in tokens:
        token = _DIRECTIONALS.get(token, token)
        token = _SUFFIXES.get(token, token)
        normalized.append(token)
    while normalized and normalized[-1] in _DROP_SUFFIX:
        normalized.pop()
    core = [token for token in normalized if token not in _DIRECTIONAL_LETTERS][:3]
    # Normalize plural/possessive on the last street-name token so "Ironwood
    # Hills" == "Ironwood Hill" and "Saint Marys" == "Saint Mary".
    if core and len(core[-1]) > 3 and core[-1].endswith("S"):
        core[-1] = core[-1][:-1]
    return " ".join(core)


def street_name_key(address: str) -> str:
    """Address key with leading house number(s) removed — the street name only.

    Used for a conservative fuzzy de-dup when sources disagree on the house
    number (e.g. CoStar address range "5220-5240" vs Yardi "5240").
    """
    tokens = address_key(address).split()
    name_tokens = [t for t in tokens if not t.isdigit()]
    return " ".join(name_tokens)
