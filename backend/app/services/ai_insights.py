from __future__ import annotations

import json
import os
from typing import Any

import requests


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def rule_based_call_prep(owner: dict[str, Any]) -> dict[str, Any]:
    top_property = owner.get("top_property", {})
    why = owner.get("why_now", "")
    property_name = top_property.get("name", "the Tucson asset")
    tax_deferral = owner.get("estimated_tax_deferral", 0)
    return {
        "source": "rule_based",
        "why_owner_may_sell": why,
        "opening_call_line": (
            f"I am calling from InTrust because your ownership group has held {property_name} long enough "
            "that a quiet, tax-aware off-market conversation may be worth exploring."
        ),
        "talking_points": [
            f"{owner.get('average_hold_period', 0):.0f}-year average hold across the Tucson position.",
            f"{owner.get('units_owned', 0)} units controlled in the market with below-market rent indicators.",
            "InTrust can discuss a direct path without a broad brokered process.",
        ],
        "possible_objections": [
            "Not interested in selling right now.",
            "Concerned about taxes and replacement options.",
            "Needs confidence around price and certainty before engaging.",
        ],
        "exchange_721_angle": (
            f"Potential 721 exchange candidate; estimated tax deferral opportunity is ${tax_deferral:,.0f}."
            if owner.get("potential_721_candidate")
            else "721 exchange angle is secondary unless the owner raises tax friction or succession planning."
        ),
    }


def _extract_output_text(payload: dict[str, Any]) -> str:
    if payload.get("output_text"):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks)


def generate_ai_call_prep(owner: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return rule_based_call_prep(owner)

    top_property = owner.get("top_property", {})
    prompt = {
        "owner": owner.get("owner"),
        "mailing_address": owner.get("mailing_address"),
        "owner_state": owner.get("owner_state"),
        "properties_owned": owner.get("properties_owned"),
        "units_owned": owner.get("units_owned"),
        "average_hold_period": owner.get("average_hold_period"),
        "oldest_acquisition": owner.get("oldest_acquisition"),
        "newest_acquisition": owner.get("newest_acquisition"),
        "call_score": owner.get("call_score"),
        "fit_score": owner.get("fit_score"),
        "motivation_score": owner.get("motivation_score"),
        "potential_721_candidate": owner.get("potential_721_candidate"),
        "estimated_tax_deferral": owner.get("estimated_tax_deferral"),
        "why_now": owner.get("why_now"),
        "recommended_angle": owner.get("recommended_angle"),
        "top_property": {
            "name": top_property.get("name"),
            "address": top_property.get("address"),
            "units": top_property.get("units"),
            "year_built": top_property.get("year_built"),
            "rent_gap": top_property.get("rent_gap"),
            "basis_gap": top_property.get("basis_gap"),
        },
    }
    body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.5"),
        "store": False,
        "instructions": (
            "You are an acquisitions associate at InTrust Property Group. "
            "Write concise, practical call prep for an off-market multifamily owner. "
            "Do not change scores or invent facts. Return valid JSON only with keys: "
            "why_owner_may_sell, opening_call_line, talking_points, possible_objections, exchange_721_angle."
        ),
        "input": f"Generate AI call prep from this owner context:\n{json.dumps(prompt, indent=2)}",
        "text": {"format": {"type": "json_object"}},
    }
    try:
        response = requests.post(
            OPENAI_RESPONSES_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=18,
        )
        response.raise_for_status()
        text = _extract_output_text(response.json())
        parsed = json.loads(text)
        return {"source": "openai", **parsed}
    except Exception:
        return rule_based_call_prep(owner)

