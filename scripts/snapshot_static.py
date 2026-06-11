"""Snapshot the live API into static JSON for a backend-free (Vercel) deploy.

Run with the backend running locally:
    python scripts/snapshot_static.py

Writes frontend/public/data/*.json. The frontend serves these when no
NEXT_PUBLIC_API_BASE is configured (i.e. on a static Vercel deploy).
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data"

ENDPOINTS = {
    "summary": "/api/market/summary",
    "context": "/api/market/context",
    "markets": "/api/markets",
    "today-call-list": "/api/today-call-list?data_scope=live",
    "map": "/api/map?data_scope=live",
    "debt-watch": "/api/debt-watch?data_scope=live&limit=400",
    "pipeline": "/api/pipeline",
    "opportunities-all": "/api/opportunities?data_scope=live&intrust_mode=false&limit=500",
    "opportunities-intrust": "/api/opportunities?data_scope=live&intrust_mode=true&limit=500",
    "owners-all": "/api/owners?data_scope=live&intrust_mode=false&limit=500",
    "owners-intrust": "/api/owners?data_scope=live&intrust_mode=true&limit=500",
}


def fetch(path: str):
    with urllib.request.urlopen(BASE + path, timeout=60) as response:
        return json.loads(response.read())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in ENDPOINTS.items():
        data = fetch(path)
        (OUT / f"{name}.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        size = (OUT / f"{name}.json").stat().st_size
        count = len(data) if isinstance(data, list) else "obj"
        print(f"  {name}.json  ({count} items, {size // 1024} KB)")
    print(f"Wrote snapshot to {OUT}")


if __name__ == "__main__":
    main()
