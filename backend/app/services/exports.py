from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Any

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from backend.app.services.ranking import get_ranked_properties, get_today_call_list


def build_opportunities_csv(db: Session) -> str:
    rows = get_ranked_properties(db, limit=200)
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "data_status",
            "is_demo",
            "match_status",
            "call_score",
            "fit_score",
            "motivation_score",
            "recommendation",
            "property",
            "owner",
            "owner_phone",
            "owner_email",
            "units",
            "year_built",
            "hold_period",
            "owner_state",
            "rent_gap",
            "assessed_value",
            "potential_721_candidate",
            "estimated_tax_deferral",
            "why_now",
            "recommended_angle",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "data_status": row.get("data_status", ""),
                "is_demo": "DEMO" if row.get("data_status") == "seeded_fallback" else "",
                "match_status": row.get("match_status", ""),
                "call_score": row["call_score"],
                "fit_score": row["fit_score"],
                "motivation_score": row["motivation_score"],
                "recommendation": row["recommendation"],
                "property": row["name"],
                "owner": row["owner_name"],
                "owner_phone": row.get("owner_phone", ""),
                "owner_email": row.get("owner_email", ""),
                "units": row["units"],
                "year_built": row["year_built"],
                "hold_period": row["hold_period"],
                "owner_state": row["owner_state"],
                "rent_gap": row["rent_gap"],
                "assessed_value": row["assessed_value"],
                "potential_721_candidate": row["potential_721_candidate"],
                "estimated_tax_deferral": row["estimated_tax_deferral"],
                "why_now": row["why_now"],
                "recommended_angle": row["recommended_angle"],
            }
        )
    return output.getvalue()


# Paragraph styles so long cells (owner, property, why-call) wrap within their
# column instead of overflowing the page.
_CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=7, leading=8.5, textColor=colors.HexColor("#111111"))
_HEAD = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.HexColor("#E8C15A"))


def _p(text: Any, style: ParagraphStyle = _CELL) -> Paragraph:
    return Paragraph(escape(str(text)), style)


def _call_list_table(title: str, rows: list[dict[str, Any]], owner_rows: bool = True) -> list[Any]:
    styles = getSampleStyleSheet()
    story: list[Any] = [Paragraph(title, styles["Heading2"])]
    headers = ["Owner", "Phone", "Property", "Units", "Held", "Call", "Why Call"]
    data = [[_p(h, _HEAD) for h in headers]]
    for row in rows:
        prop = row.get("top_property", row) if owner_rows else row
        phone = row.get("owner_phone") or prop.get("owner_phone", "") or "-"
        data.append(
            [
                _p(row.get("owner", row.get("owner_name", ""))),
                _p(phone),
                _p(prop.get("name", "")),
                _p(row.get("units_owned", prop.get("units", ""))),
                _p(f"{row.get('average_hold_period', prop.get('hold_period', 0)):.0f}"),
                _p(f"{row.get('call_score', prop.get('call_score', 0)):.1f}"),
                _p(row.get("why_now", prop.get("why_now", ""))),
            ]
        )
    # Widths sum to ~724pt, within landscape-letter usable width (~744pt).
    table = Table(data, repeatRows=1, colWidths=[96, 70, 96, 34, 34, 34, 360])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#555555")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8F8F8"), colors.white]),
            ]
        )
    )
    story.extend([table, Spacer(1, 12)])
    return story


def build_today_call_list_pdf(db: Session) -> bytes:
    call_list = get_today_call_list(db)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24,
        title="InTrust Today Call List - Tucson",
    )
    styles = getSampleStyleSheet()
    story: list[Any] = [
        Paragraph("InTrust Tucson Today's Call List", styles["Title"]),
        Paragraph(
            "Owner-first off-market acquisition priorities. Sorted by Call Score: 50% Fit Score + 50% Motivation Score.",
            styles["BodyText"],
        ),
        Spacer(1, 10),
    ]
    story.extend(_call_list_table("Top 10 Owners", call_list["top_10_owners"], owner_rows=True))
    story.extend(_call_list_table("Top New Opportunities", call_list["top_new_opportunities"], owner_rows=False))
    story.extend(_call_list_table("Top 25 Owners", call_list["top_25_owners"], owner_rows=True))
    doc.build(story)
    return buffer.getvalue()

