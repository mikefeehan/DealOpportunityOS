from __future__ import annotations

from urllib.parse import unquote

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.database import Base, engine, get_db
from backend.app.models import Pipeline, Property
from backend.app.services.ai_insights import generate_ai_call_prep
from backend.app.services.exports import build_opportunities_csv, build_today_call_list_pdf
from backend.app.services.ranking import (
    get_market_summary,
    get_owner_profile,
    get_owner_profiles,
    get_ranked_properties,
    get_today_call_list,
    property_to_dict,
)
from backend.app.services.scanner import run_tucson_scan
from backend.app.services.scoring import PIPELINE_STAGES
from backend.app.services.seed_data import ensure_seed_data


app = FastAPI(title="OpportunityOS Tucson Pilot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PipelineUpdate(BaseModel):
    stage: str | None = None
    notes: str | None = None


class CallPrepRequest(BaseModel):
    owner_name: str


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        ensure_seed_data(db)


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    return {"status": "ok", "properties": db.query(Property).count()}


@app.post("/api/scan/tucson")
def scan_tucson(db: Session = Depends(get_db)) -> dict:
    return run_tucson_scan(db)


@app.get("/api/market/summary")
def market_summary(db: Session = Depends(get_db)) -> dict:
    return get_market_summary(db)


@app.get("/api/today-call-list")
def today_call_list(db: Session = Depends(get_db)) -> dict:
    return get_today_call_list(db)


@app.get("/api/opportunities")
def opportunities(
    q: str | None = None,
    stage: str | None = None,
    recommendation: str | None = None,
    min_score: float | None = None,
    intrust_mode: bool = Query(False),
    limit: int | None = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    return get_ranked_properties(
        db,
        q=q,
        stage=stage,
        min_score=min_score,
        intrust_mode=intrust_mode,
        recommendation=recommendation,
        limit=limit,
    )


@app.get("/api/owners")
def owners(
    intrust_mode: bool = Query(False),
    limit: int | None = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    return get_owner_profiles(db, intrust_mode=intrust_mode, limit=limit)


@app.get("/api/owners/{owner_name:path}")
def owner_detail(owner_name: str, db: Session = Depends(get_db)) -> dict:
    owner = get_owner_profile(db, unquote(owner_name))
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    return owner


@app.get("/api/properties/{property_id}")
def property_detail(property_id: int, db: Session = Depends(get_db)) -> dict:
    stmt = (
        select(Property)
        .options(joinedload(Property.score), joinedload(Property.pipeline))
        .where(Property.id == property_id)
    )
    prop = db.scalar(stmt)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_to_dict(prop)


@app.get("/api/pipeline")
def pipeline(db: Session = Depends(get_db)) -> dict:
    props = get_ranked_properties(db)
    grouped = {stage: [] for stage in PIPELINE_STAGES}
    for prop in props:
        grouped.setdefault(prop["stage"], []).append(prop)
    return {"stages": PIPELINE_STAGES, "properties_by_stage": grouped}


@app.patch("/api/pipeline/{property_id}")
def update_pipeline(property_id: int, payload: PipelineUpdate, db: Session = Depends(get_db)) -> dict:
    prop = db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    row = db.get(Pipeline, property_id)
    if not row:
        row = Pipeline(property_id=property_id, stage="Identified", notes="")
        db.add(row)
    if payload.stage:
        if payload.stage not in PIPELINE_STAGES:
            raise HTTPException(status_code=400, detail=f"Stage must be one of {', '.join(PIPELINE_STAGES)}")
        row.stage = payload.stage
    if payload.notes is not None:
        row.notes = payload.notes
    db.commit()
    db.refresh(row)
    return {"property_id": property_id, "stage": row.stage, "notes": row.notes}


@app.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)) -> Response:
    csv_payload = build_opportunities_csv(db)
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=intrust_tucson_opportunities.csv"},
    )


@app.get("/api/export/today-call-list.pdf")
def export_today_call_list_pdf(db: Session = Depends(get_db)) -> Response:
    pdf_payload = build_today_call_list_pdf(db)
    return Response(
        content=pdf_payload,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=intrust_tucson_today_call_list.pdf"},
    )


@app.post("/api/ai/call-prep")
def ai_call_prep(payload: CallPrepRequest, db: Session = Depends(get_db)) -> dict:
    owner = get_owner_profile(db, payload.owner_name)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    return generate_ai_call_prep(owner)
