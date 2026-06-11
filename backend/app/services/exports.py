from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
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


def _call_list_table(title: str, rows: list[dict[str, Any]], owner_rows: bool = True) -> list[Any]:
    styles = getSampleStyleSheet()
    story: list[Any] = [Paragraph(title, styles["Heading2"])]
    header = ["Owner", "Property", "Units", "Years Held", "Call Score", "Why Call"]
    data = [header]
    for row in rows:
        prop = row.get("top_property", row) if owner_rows else row
        data.append(
            [
                row.get("owner", row.get("owner_name", ""))[:28],
                prop.get("name", "")[:28],
                str(row.get("units_owned", prop.get("units", ""))),
                f"{row.get('average_hold_period', prop.get('hold_period', 0)):.0f}",
                f"{row.get('call_score', prop.get('call_score', 0)):.1f}",
                row.get("why_now", prop.get("why_now", ""))[:90],
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[120, 120, 45, 58, 58, 260])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#E8C15A")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#555555")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
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

