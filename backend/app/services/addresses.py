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

# Trailing tokens to drop when building the key (street type words).
_DROP_SUFFIX = set(_SUFFIXES.values()) | {
    "WAY", "LOOP", "PASS", "PT", "SQ", "ROW", "RUN", "BEND", "PASEO", "VIA",
    "CAMINO", "PLAZA", "PIKE", "PATH", "CROSSING", "WALK",
}


def address_key(address: str) -> str:
    """Stable join key: house number + up to two normalized street-name tokens."""
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
    return " ".join(normalized[:3])
