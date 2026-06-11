"""Owner email enrichment via Hunter.io.

The source exports already give a phone for nearly every owner; the gap is email.
For owners that have a website (e.g. Yardi "Owner Website") but no email, this
runs a Hunter.io domain search and attaches the best match — preferring a person
whose name matches the owner contact, else the highest-confidence address.

Key from HUNTER_API_KEY (env or repo-root .env). Runs server-side, on demand,
batched, with a limit so it doesn't burn search credits.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Property

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"
DOMAIN_SEARCH_URL = "https://api.hunter.io/v2/domain-search"


def get_hunter_key() -> str:
    key = os.getenv("HUNTER_API_KEY", "").strip()
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.match(r"\s*HUNTER_API_KEY\s*=\s*(.+)\s*$", line)
            if match:
                return match.group(1).strip().strip('"').strip("'")
    return ""


def website_to_domain(website: str) -> str:
    text = (website or "").strip().lower()
    if not text or "." not in text:
        return ""
    if "://" not in text:
        text = "http://" + text
    host = urlparse(text).netloc or urlparse(text).path
    host = host.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host if "." in host else ""


def _pick_email(emails: list[dict], contact_name: str) -> str:
    if not emails:
        return ""
    last = (contact_name or "").strip().split()[-1].lower() if contact_name else ""
    # Prefer a personal address whose last name matches the owner contact.
    if last:
        for entry in emails:
            if entry.get("type") == "personal" and last and last in (entry.get("last_name") or "").lower():
                return entry.get("value", "")
    personal = [e for e in emails if e.get("type") == "personal"]
    pool = personal or emails
    pool = sorted(pool, key=lambda e: e.get("confidence") or 0, reverse=True)
    return pool[0].get("value", "") if pool else ""


def hunter_domain_search(domain: str, key: str, contact_name: str) -> str:
    try:
        response = requests.get(
            DOMAIN_SEARCH_URL,
            params={"domain": domain, "api_key": key, "limit": 10},
            timeout=12,
        )
        if response.status_code != 200:
            return ""
        data = response.json().get("data") or {}
    except Exception:  # noqa: BLE001
        return ""
    return _pick_email(data.get("emails") or [], contact_name)


def enrich_emails(db: Session, market: str | None = None, limit: int = 25) -> dict[str, Any]:
    key = get_hunter_key()
    if not key:
        return {"status": "error", "error": "No HUNTER_API_KEY set.", "found": 0}

    stmt = select(Property).where(Property.data_status != "seeded_fallback")
    if market:
        stmt = stmt.where(Property.market == market)
    props = list(db.scalars(stmt).all())

    # One lookup per domain; apply the result to every property of that owner.
    by_domain: dict[str, list[Property]] = {}
    for prop in props:
        if prop.owner_email or not prop.owner_website:
            continue
        domain = website_to_domain(prop.owner_website)
        if domain:
            by_domain.setdefault(domain, []).append(prop)

    domains = list(by_domain.items())
    searched = 0
    found = 0
    for domain, owned in domains[:limit]:
        searched += 1
        contact = next((p.owner_contact for p in owned if p.owner_contact), "")
        email = hunter_domain_search(domain, key, contact)
        if not email:
            continue
        owner_names = {p.owner_name for p in owned}
        for prop in props:
            if prop.owner_name in owner_names and not prop.owner_email:
                prop.owner_email = email
                found += 1
    db.commit()
    return {
        "status": "ok",
        "candidate_domains": len(domains),
        "searched": searched,
        "emails_applied": found,
        "remaining_domains": max(0, len(domains) - searched),
    }
