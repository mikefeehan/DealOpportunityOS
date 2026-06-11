"""Market context from a HelloData Market Analytics report.

Parses the headline market metrics (rents, rent growth, supply pipeline,
demographics) out of a HelloData market-analytics PDF dropped in
``data/market_reference/`` and supplements them with comp-set stats from the CSV
reference. Used by the Command Center to answer "is this a market to buy into?"

Everything degrades gracefully: missing report or unparseable field -> None.
"""

from __future__ import annotations

import os
import re
import statistics
from functools import lru_cache
from pathlib import Path

from backend.app.services.market_reference import MARKET_REF_DIR, load_market_reference


def _num(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[\d,]+(\.\d+)?", value)
    return float(match.group(0).replace(",", "")) if match else None


def _last_int_on_line(text: str, label: str) -> float | None:
    match = re.search(rf"{re.escape(label)}\([\d.]+%\)\s*([^\n]+)", text)
    if not match:
        return None
    ints = re.findall(r"[\d,]{2,}", match.group(1))
    return float(ints[-1].replace(",", "")) if ints else None


def _candidate_pdf() -> Path | None:
    env = os.getenv("MARKET_CONTEXT_PDF")
    if env and Path(env).exists():
        return Path(env)
    if MARKET_REF_DIR.exists():
        pdfs = sorted(MARKET_REF_DIR.glob("*.pdf"))
        if pdfs:
            return pdfs[-1]
    return None


def _parse_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:  # noqa: BLE001
        return ""
    try:
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:  # noqa: BLE001
        return ""


def _search(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else None


@lru_cache(maxsize=1)
def load_market_context() -> dict:
    ref = load_market_reference()
    comp_rents = list(ref["by_street"].values())
    context: dict = {
        "available": False,
        "as_of": None,
        "source": "HelloData Market Analytics",
        "rent": {},
        "supply": {},
        "demographics": {},
        "comp_set": {
            "properties": ref["count"] or None,
            "median_rent": round(statistics.median(comp_rents)) if comp_rents else None,
        },
    }

    pdf = _candidate_pdf()
    if not pdf:
        context["available"] = bool(comp_rents)
        return context
    text = _parse_pdf_text(pdf)
    if not text:
        context["available"] = bool(comp_rents)
        return context

    asking = _num(_search(text, r"Average Asking Rent\s*\$?([\d,]+)"))
    effective = _num(_search(text, r"Average Effective Rent\s*\$?([\d,]+)"))
    concession_pct = round((asking - effective) / asking * 100, 1) if asking and effective else None
    context["rent"] = {
        "avg_asking": asking,
        "avg_effective": effective,
        "concession_pct": concession_pct,
        "growth_yoy": _num(_search(text, r"Growth:\s*Market\s*\(Median\)\s*([+\-]?[\d.]+)%")),
    }

    size = re.search(r"Properties\s+([\d,]+)\s+Units\s+([\d,]+)", text)
    context["supply"] = {
        "existing_properties": _num(size.group(1)) if size else None,
        "existing_units": _num(size.group(2)) if size else None,
        "in_planning_units": _last_int_on_line(text, "In Planning"),
        "under_construction_units": _last_int_on_line(text, "Under Construction"),
        "pipeline_total_units": _last_int_on_line(text, "Total"),
    }

    context["demographics"] = {
        "population": _num(_search(text, r"Total Population\(\d+\)\s*([\d,]+)")),
        "median_income": _num(_search(text, r"Current Median Income\(\d+\)\s*([\d,]+)")),
        "employment_rate": _num(_search(text, r"Employment Rate\(\d+\)\s*([\d.]+)%")),
    }

    report_date = _search(text, r"Report Date:\s*([\d/]+)")
    context["as_of"] = report_date
    context["available"] = True
    return context
