from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from backend.app.services.ranking import (
    get_debt_opportunities,
    get_ranked_properties,
    get_today_call_list,
)

# InTrust brand palette (from brand guidelines).
BRAND_BLUE = colors.HexColor("#12648a")  # PMS 7706
BRAND_GREY = colors.HexColor("#a1a0a0")  # PMS 422
BRAND_ROW = colors.HexColor("#eef3f6")   # light blue-grey for alternating rows
_LOGO_PATH = Path(__file__).resolve().parents[3] / "frontend" / "public" / "brand" / "intrust-color.png"


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
_CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=7, leading=8.5, textColor=colors.HexColor("#1a1a1a"))
_HEAD = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.white)
_SECTION = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=BRAND_BLUE, spaceBefore=4, spaceAfter=4)


def _p(text: Any, style: ParagraphStyle = _CELL) -> Paragraph:
    return Paragraph(escape(str(text)), style)


def _call_list_table(title: str, rows: list[dict[str, Any]], owner_rows: bool = True) -> list[Any]:
    story: list[Any] = [Paragraph(title, _SECTION)]
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
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
                ("GRID", (0, 0), (-1, -1), 0.4, BRAND_GREY),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, BRAND_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRAND_ROW, colors.white]),
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
    title_style = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=BRAND_BLUE, spaceAfter=2
    )
    sub_style = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, leading=12, textColor=BRAND_GREY)
    story: list[Any] = []
    if _LOGO_PATH.exists():
        width, height = ImageReader(str(_LOGO_PATH)).getSize()
        logo = Image(str(_LOGO_PATH), width=150, height=150 * height / width)
        logo.hAlign = "LEFT"
        story.extend([logo, Spacer(1, 6)])
    story.extend(
        [
            Paragraph("Today's Call List", title_style),
            Paragraph(
                "Owner-first off-market acquisition priorities. Sorted by Call Score: 50% Fit Score + 50% Motivation Score.",
                sub_style,
            ),
            Spacer(1, 10),
        ]
    )
    story.extend(_call_list_table("Top 10 Owners", call_list["top_10_owners"], owner_rows=True))
    story.extend(_call_list_table("Top New Opportunities", call_list["top_new_opportunities"], owner_rows=False))
    story.extend(_call_list_table("Top 25 Owners", call_list["top_25_owners"], owner_rows=True))
    doc.build(story)
    return buffer.getvalue()


_CELL_RED = ParagraphStyle("cellred", fontName="Helvetica-Bold", fontSize=7, leading=8.5, textColor=colors.HexColor("#c0392b"))


def _money(value: float) -> str:
    if not value:
        return "-"
    return f"${value / 1_000_000:.1f}M" if value >= 1_000_000 else f"${value:,.0f}"


def _pdf_header(title: str, subtitle: str) -> list[Any]:
    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=BRAND_BLUE, spaceAfter=2)
    sub_style = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, leading=12, textColor=BRAND_GREY)
    story: list[Any] = []
    if _LOGO_PATH.exists():
        width, height = ImageReader(str(_LOGO_PATH)).getSize()
        logo = Image(str(_LOGO_PATH), width=150, height=150 * height / width)
        logo.hAlign = "LEFT"
        story.extend([logo, Spacer(1, 6)])
    story.extend([Paragraph(title, title_style), Paragraph(subtitle, sub_style), Spacer(1, 10)])
    return story


def build_maturing_debt_pdf(db: Session) -> bytes:
    rows = get_debt_opportunities(db, data_scope="live", limit=50)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24,
        title="InTrust Maturing Debt",
    )
    story = _pdf_header(
        "Maturing Debt - Refinance Opportunities",
        "Owners facing a loan maturity or thin coverage. Ranked by debt pressure. DSCR below 1.20x in red.",
    )
    headers = ["Property", "Owner", "Phone", "Units", "Maturity", "Rate", "DSCR", "Loan", "Lender", "Why Now"]
    data = [[_p(h, _HEAD) for h in headers]]
    for row in rows:
        dscr = row.get("dscr") or 0
        dscr_cell = _p(f"{dscr:.2f}" if dscr else "-", _CELL_RED if dscr and dscr < 1.2 else _CELL)
        data.append(
            [
                _p(row.get("name", "")),
                _p(row.get("owner_name", "")),
                _p(row.get("owner_phone") or "-"),
                _p(row.get("units", "")),
                _p(row.get("loan_maturity_year") or "-"),
                _p(f"{row['interest_rate']:.2f}%" if row.get("interest_rate") else "-"),
                dscr_cell,
                _p(_money(row.get("loan_amount", 0))),
                _p(row.get("lender") or "-"),
                _p(row.get("why_now", "")),
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[90, 82, 62, 28, 42, 34, 34, 48, 86, 232])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
                ("GRID", (0, 0), (-1, -1), 0.4, BRAND_GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRAND_ROW, colors.white]),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()

