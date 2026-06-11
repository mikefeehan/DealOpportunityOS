#!/usr/bin/env python3
"""owner-tracer — semi-automate finding Tucson / Pima County multifamily owner contacts, free.

Pipeline per property:
  1. Pima County Assessor parcel lookup (automated ArcGIS REST query) -> owner,
     mailing address, APN, legal class, units.
  2. Entity resolution (Arizona) -> if the owner is an LLC/LP/Trust/etc., pull
     members/agent from OpenCorporates and deep-link the AZ Corporation
     Commission (Arizona Business Center; legacy eCorp).
  3. Contact search links (one click) -> TruePeopleSearch, FastPeopleSearch,
     Google, LinkedIn for each principal.
  4. Logging -> prompt for any phone/email found and append to tracker.csv.

Free APIs only (Pima ArcGIS REST, OpenCorporates free tier). requests + stdlib + rich.

Usage:
    python tracer.py "4444 E Grant Rd, Tucson, AZ"
    python tracer.py --apn 116-05-009A
    python tracer.py --csv list.csv            # bulk -> enriched_<list>.csv
    python tracer.py "..." --open              # also open search links in browser
    python tracer.py "..." --no-prompt         # skip the phone/email prompt
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import webbrowser
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

import requests

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError:  # pragma: no cover
    print("This tool needs 'rich'. Install with:  pip install rich requests")
    sys.exit(1)

# Windows' legacy console is cp1252 and chokes on non-ASCII (owner names, etc.).
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        pass

console = Console()

# --- Endpoints ------------------------------------------------------------

# Pima County Assessor county-wide parcel layer (PAREGION). Hosted on the City of
# Tucson ArcGIS server, it covers City of Tucson + unincorporated Pima County.
# If this ever moves, see README for how to find the current layer.
PIMA_PARCEL_LAYERS = [
    "https://mapdata.tucsonaz.gov/public/rest/services/PublicMaps/PropertyHousing/MapServer/17/query",
]
PIMA_ASSESSOR_SEARCH = "https://www.asr.pima.gov/advanced-search"
PIMA_PARCEL_VIEWER = "https://gis.pima.gov/parcels/"

# AZ Corporation Commission. eCorp (ecorp.azcc.gov) was decommissioned 2026-01-02;
# the live portal is Arizona Business Center. We deep-link both for convenience.
AZ_BUSINESS_CENTER = "https://arizonabusinesscenter.azcc.gov/businesssearch"
AZ_ECORP_LEGACY = "https://ecorp.azcc.gov/EntitySearch/Index"

OPENCORPORATES_SEARCH = "https://api.opencorporates.com/v0.4/companies/search"
OPENCORPORATES_COMPANY = "https://api.opencorporates.com/v0.4/companies"

HEADERS = {"User-Agent": "owner-tracer/1.0 (research; contact via local use)"}
TRACKER_CSV = Path(__file__).resolve().parent / "tracker.csv"

ENTITY_TOKENS = [
    "LLC", "L.L.C", "L L C", "LP", "L.P.", "LLP", "LTD", "INC", "INCORPORATED",
    "CORP", "CORPORATION", "COMPANY", " CO ", "TRUST", "PARTNERS", "PARTNERSHIP",
    "HOLDINGS", "PROPERTIES", "ASSOCIATES", "VENTURES", "GROUP", "FUND",
    "INVESTMENTS", "INVESTMENT", "CAPITAL", "ENTERPRISES", "REALTY", "MANAGEMENT",
    "DEVELOPMENT", "ESTATE",
]


# --- Helpers --------------------------------------------------------------

def _first(attrs: dict, *names, default=""):
    for name in names:
        if name in attrs and attrs[name] not in (None, ""):
            return attrs[name]
    return default


def is_entity(owner_name: str) -> bool:
    upper = f" {(owner_name or '').upper()} "
    return any(token in upper for token in ENTITY_TOKENS)


def normalize_apn(apn: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", (apn or "")).upper()


def address_token(address: str) -> str:
    head = (address or "").split(",")[0].upper().strip()
    head = re.sub(r"[^A-Z0-9 ]", " ", head)
    parts = [p for p in head.split() if p]
    return " ".join(parts[:3]) if len(parts) >= 3 else " ".join(parts)


# --- Step 1: Pima parcel lookup ------------------------------------------

def _query_pima(where: str) -> dict | None:
    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": 1,
    }
    for url in PIMA_PARCEL_LAYERS:
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=12)
            response.raise_for_status()
            features = response.json().get("features", [])
        except Exception as exc:  # noqa: BLE001
            console.print(f"[yellow]Pima query failed ({url.split('/rest')[0]}): {exc}[/yellow]")
            continue
        if features:
            return features[0].get("attributes") or {}
    return None


def pima_lookup(address: str | None = None, apn: str | None = None) -> dict | None:
    if apn:
        clean = normalize_apn(apn)
        # PAREGION stores APNs with and without dashes across deployments; try both.
        attrs = _query_pima(f"PARCEL='{clean}'") or _query_pima(f"PARCEL='{apn}'")
    else:
        token = address_token(address or "").replace("'", "''")
        if not token:
            return None
        attrs = _query_pima(f"UPPER(SITE_ADDRESS) LIKE '%{token}%'")
    if not attrs:
        return None

    mailing_parts = [
        str(_first(attrs, field)).strip()
        for field in ["MAIL1", "MAIL2", "MAIL3", "MAIL4", "MAIL5"]
        if _first(attrs, field)
    ]
    return {
        "apn": str(_first(attrs, "PARCEL", "Parcel", "APN", "PIN")).strip(),
        "owner": str(_first(attrs, "ADDRESSEE", "OWNER", "OWNER_NAME", default="Unknown")).strip(),
        "site_address": str(_first(attrs, "SITE_ADDRESS", "SITUSADDR", "ADDRESS")).strip(),
        "mailing_address": ", ".join(mailing_parts) or "(not listed)",
        "legal_class": str(_first(attrs, "USE_DESC", "LEGAL_CLASS", "PEPropertyType")).strip() or "(n/a)",
        "units": _first(attrs, "UNITS", "Units", "NO_UNITS", default=""),
        "year_built": _first(attrs, "YearBuilt", "YEARBUILT", "YR_BUILT", default=""),
        "full_cash_value": _first(attrs, "FCV", "FULL_CASH_VALUE", default=""),
    }


def mailing_city_state(mailing_address: str) -> tuple[str, str]:
    """Best-effort parse of 'City ST ZIP' from the last line of a mailing address."""
    last = (mailing_address or "").split(",")[-1].strip()
    match = re.search(r"([A-Za-z .]+)\s+([A-Z]{2})\s+\d{5}", mailing_address or "")
    if match:
        return match.group(1).strip(), match.group(2)
    tokens = last.split()
    state = next((t for t in tokens if len(t) == 2 and t.isalpha() and t.isupper()), "")
    return "", state


# --- Step 2: Entity resolution -------------------------------------------

def opencorporates_lookup(name: str) -> dict | None:
    """Free OpenCorporates search + officer pull for an AZ entity. Degrades to None."""
    try:
        response = requests.get(
            OPENCORPORATES_SEARCH,
            params={"q": name, "jurisdiction_code": "us_az", "per_page": 1},
            headers=HEADERS,
            timeout=12,
        )
        if response.status_code != 200:
            return None
        companies = response.json().get("results", {}).get("companies", [])
    except Exception:  # noqa: BLE001
        return None
    if not companies:
        return None
    company = companies[0]["company"]
    result = {
        "name": company.get("name"),
        "company_number": company.get("company_number"),
        "jurisdiction": company.get("jurisdiction_code"),
        "status": company.get("current_status"),
        "address": company.get("registered_address_in_full"),
        "officers": [],
        "opencorporates_url": company.get("opencorporates_url"),
    }
    # Pull officers/agent from the company detail endpoint.
    try:
        detail = requests.get(
            f"{OPENCORPORATES_COMPANY}/{result['jurisdiction']}/{result['company_number']}",
            headers=HEADERS,
            timeout=12,
        )
        if detail.status_code == 200:
            officers = detail.json().get("results", {}).get("company", {}).get("officers", [])
            for entry in officers:
                officer = entry.get("officer", {})
                result["officers"].append(
                    {
                        "name": officer.get("name"),
                        "position": officer.get("position") or "",
                        "address": officer.get("address") or "",
                    }
                )
    except Exception:  # noqa: BLE001
        pass
    return result


def az_corp_links(entity_name: str) -> dict:
    q = quote_plus(entity_name)
    return {
        "Arizona Business Center (current)": f"{AZ_BUSINESS_CENTER}?searchTerm={q}",
        "eCorp (legacy)": AZ_ECORP_LEGACY,
    }


# --- Step 3: Contact search links ----------------------------------------

def people_links(person: str, city: str, state: str, entity: str = "") -> dict:
    name_q = quote_plus(person)
    citystate = quote_plus(f"{city}, {state}".strip(", "))
    fps_slug = re.sub(r"[^a-z0-9]+", "-", person.lower()).strip("-")
    fps_loc = re.sub(r"[^a-z0-9]+", "-", f"{city} {state}".lower()).strip("-")
    entity_q = f'"{entity}"' if entity else ""
    google = quote_plus(f'"{person}" {entity_q} phone'.strip())
    return {
        "TruePeopleSearch": f"https://www.truepeoplesearch.com/results?name={name_q}&citystatezip={citystate}",
        "FastPeopleSearch": f"https://www.fastpeoplesearch.com/name/{fps_slug}_{fps_loc}".rstrip("_"),
        "Google": f"https://www.google.com/search?q={google}",
        "LinkedIn": f"https://www.linkedin.com/search/results/people/?keywords={name_q}",
    }


# --- Orchestration --------------------------------------------------------

def render(parcel: dict, entity_data: dict | None, principals: list[str], links_by_person: dict) -> None:
    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="white")
    table.add_row("APN", parcel["apn"] or "(n/a)")
    table.add_row("Owner / addressee", f"[bold]{parcel['owner']}[/bold]")
    table.add_row("Site address", parcel["site_address"] or "(n/a)")
    mail = parcel["mailing_address"]
    differs = mail and parcel["site_address"] and address_token(mail) != address_token(parcel["site_address"])
    table.add_row(
        "Mailing address",
        f"[bold yellow]{mail}  <- differs from property (likely principal's home/office)[/bold yellow]" if differs else mail,
    )
    table.add_row("Legal class / use", parcel["legal_class"])
    if parcel["units"]:
        table.add_row("Units", str(parcel["units"]))
    if parcel["year_built"]:
        table.add_row("Year built", str(parcel["year_built"]))
    if parcel["full_cash_value"]:
        table.add_row("Full cash value", str(parcel["full_cash_value"]))
    console.print(Panel(table, title="[bold]1 - Pima County parcel[/bold]", border_style="cyan"))

    if is_entity(parcel["owner"]):
        ent = Table(box=box.SIMPLE, show_header=False)
        ent.add_column(style="cyan", no_wrap=True)
        ent.add_column(style="white")
        if entity_data:
            ent.add_row("Matched entity", entity_data.get("name") or "—")
            ent.add_row("Status", entity_data.get("status") or "—")
            ent.add_row("Registered address", entity_data.get("address") or "—")
            if entity_data.get("officers"):
                for off in entity_data["officers"]:
                    ent.add_row("Member / agent", f"[bold]{off['name']}[/bold]  {off['position']}  {off['address']}")
            if entity_data.get("opencorporates_url"):
                ent.add_row("OpenCorporates", entity_data["opencorporates_url"])
        else:
            ent.add_row("OpenCorporates", "[yellow]no free match — use the AZCC links below[/yellow]")
        for label, url in az_corp_links(parcel["owner"]).items():
            ent.add_row(label, url)
        console.print(Panel(ent, title="[bold]2 - Arizona entity resolution[/bold]", border_style="magenta"))
    else:
        console.print(Panel("[white]Individual owner — skipping entity step.[/white]",
                            title="[bold]2 - Arizona entity resolution[/bold]", border_style="magenta"))

    for person, links in links_by_person.items():
        link_table = Table(box=box.SIMPLE, show_header=False)
        link_table.add_column(style="cyan", no_wrap=True)
        link_table.add_column(style="blue underline")
        for label, url in links.items():
            link_table.add_row(label, url)
        console.print(Panel(link_table, title=f"[bold]3 - Contact search - {person}[/bold]", border_style="green"))


def trace(query: str | None, apn: str | None, open_links: bool, prompt: bool) -> dict:
    label = apn or query
    console.rule(f"[bold]owner-tracer - {label}[/bold]")
    parcel = pima_lookup(address=query, apn=apn)
    if not parcel:
        console.print("[red]No Pima parcel match.[/red] Try the manual search:")
        console.print(f"  Assessor advanced search: {PIMA_ASSESSOR_SEARCH}")
        console.print(f"  Parcel viewer:            {PIMA_PARCEL_VIEWER}")
        return {"address": label, "apn": apn or "", "owner": "", "principals": "", "mailing": "",
                "phone": "", "email": "", "status": "no parcel match", "notes": ""}

    entity_data = opencorporates_lookup(parcel["owner"]) if is_entity(parcel["owner"]) else None
    city, state = mailing_city_state(parcel["mailing_address"])

    principals: list[str] = []
    if entity_data and entity_data.get("officers"):
        principals = [o["name"] for o in entity_data["officers"] if o.get("name")]
    if not principals and not is_entity(parcel["owner"]):
        principals = [parcel["owner"]]
    if not principals:
        # No officer data — still let the analyst search the entity name itself.
        principals = [parcel["owner"]]

    links_by_person = {p: people_links(p, city, state, entity=parcel["owner"]) for p in principals[:4]}
    render(parcel, entity_data, principals, links_by_person)

    if open_links:
        for links in links_by_person.values():
            for url in links.values():
                webbrowser.open(url)

    phone = email = notes = ""
    if prompt:
        console.print()
        phone = console.input("[bold]Phone found[/bold] (enter to skip): ").strip()
        email = console.input("[bold]Email found[/bold] (enter to skip): ").strip()
        notes = console.input("[bold]Notes[/bold] (enter to skip): ").strip()

    return {
        "address": parcel["site_address"] or label,
        "apn": parcel["apn"],
        "owner": parcel["owner"],
        "principals": "; ".join(principals),
        "mailing": parcel["mailing_address"],
        "phone": phone,
        "email": email,
        "status": "traced",
        "notes": notes,
    }


# --- Step 4: Logging ------------------------------------------------------

FIELDS = ["date", "address", "apn", "owner", "principals", "mailing", "phone", "email", "status", "notes"]


def log_row(row: dict) -> None:
    row = {"date": date.today().isoformat(), **row}
    new_file = not TRACKER_CSV.exists()
    with TRACKER_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    console.print(f"[green]Logged to {TRACKER_CSV.name}[/green]\n")


# --- Bulk -----------------------------------------------------------------

def run_bulk(csv_path: Path, open_links: bool) -> None:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    out_path = csv_path.with_name(f"enriched_{csv_path.name}")
    results = []
    for entry in rows:
        addr = entry.get("address") or entry.get("Address") or entry.get("site_address") or ""
        apn = entry.get("apn") or entry.get("APN") or ""
        if not addr and not apn:
            continue
        result = trace(addr or None, apn or None, open_links=open_links, prompt=False)
        results.append(result)
        log_row(result)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS[1:], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    console.print(f"[bold green]Wrote {len(results)} enriched rows -> {out_path}[/bold green]")


# --- CLI ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Semi-automate Tucson/Pima multifamily owner contact tracing.")
    parser.add_argument("address", nargs="?", help='Property address, e.g. "4444 E Grant Rd, Tucson, AZ"')
    parser.add_argument("--apn", help="Look up by parcel/APN instead of address")
    parser.add_argument("--csv", help="Bulk: input CSV with an 'address' and/or 'apn' column")
    parser.add_argument("--open", action="store_true", help="Open the contact search links in your browser")
    parser.add_argument("--no-prompt", action="store_true", help="Skip the phone/email prompt (still logs)")
    args = parser.parse_args()

    if args.csv:
        run_bulk(Path(args.csv), open_links=args.open)
        return
    if not args.address and not args.apn:
        parser.print_help()
        return

    result = trace(args.address, args.apn, open_links=args.open, prompt=not args.no_prompt)
    log_row(result)


if __name__ == "__main__":
    main()
