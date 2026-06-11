from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parcel_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    address: Mapped[str] = mapped_column(String(255), index=True)
    units: Mapped[int] = mapped_column(Integer)
    year_built: Mapped[int] = mapped_column(Integer)
    building_sqft: Mapped[int] = mapped_column(Integer, default=0)
    avg_unit_sf: Mapped[int] = mapped_column(Integer, default=0)
    assessed_value: Mapped[float] = mapped_column(Float)
    owner_name: Mapped[str] = mapped_column(String(255), index=True)
    mailing_address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    name: Mapped[str] = mapped_column(String(255), default="")
    property_type: Mapped[str] = mapped_column(String(80), default="Apartments")
    submarket: Mapped[str] = mapped_column(String(120), default="Tucson")
    owner_city: Mapped[str] = mapped_column(String(120), default="")
    owner_state: Mapped[str] = mapped_column(String(24), default="")
    source: Mapped[str] = mapped_column(String(160), default="Seeded Tucson fallback")
    last_sale_year: Mapped[int] = mapped_column(Integer, default=2000)
    average_rent: Mapped[float] = mapped_column(Float, default=0)
    market_rent: Mapped[float] = mapped_column(Float, default=0)

    # Provenance and parcel-match confidence (set by importer / scanner).
    # data_status: seeded_fallback | live_authorized | live_public
    data_status: Mapped[str] = mapped_column(String(40), default="seeded_fallback", index=True)
    # match_status: verified | needs_review | no_match
    match_status: Mapped[str] = mapped_column(String(40), default="no_match", index=True)
    source_url: Mapped[str] = mapped_column(String(400), default="")
    source_name: Mapped[str] = mapped_column(String(160), default="")
    match_confidence: Mapped[float] = mapped_column(Float, default=0)
    matched_address: Mapped[str] = mapped_column(String(255), default="")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Cross-source aggregation + enrichment (CoStar/Yardi/HelloData merged per site).
    address_key: Mapped[str] = mapped_column(String(160), default="", index=True)
    market: Mapped[str] = mapped_column(String(120), default="Tucson, AZ", index=True)
    sources: Mapped[str] = mapped_column(String(255), default="")
    star_rating: Mapped[float] = mapped_column(Float, default=0)
    building_class: Mapped[str] = mapped_column(String(8), default="")
    location_rating: Mapped[str] = mapped_column(String(16), default="")
    cap_rate: Mapped[float] = mapped_column(Float, default=0)
    vacancy: Mapped[float] = mapped_column(Float, default=0)
    for_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    for_sale_price: Mapped[float] = mapped_column(Float, default=0)
    price_per_unit: Mapped[float] = mapped_column(Float, default=0)
    last_sale_price: Mapped[float] = mapped_column(Float, default=0)
    affordable: Mapped[bool] = mapped_column(Boolean, default=False)
    affordable_type: Mapped[str] = mapped_column(String(48), default="")
    loan_maturity_year: Mapped[int] = mapped_column(Integer, default=0)
    interest_rate: Mapped[float] = mapped_column(Float, default=0)
    loan_amount: Mapped[float] = mapped_column(Float, default=0)
    lender: Mapped[str] = mapped_column(String(120), default="")
    year_renovated: Mapped[int] = mapped_column(Integer, default=0)
    effective_rent: Mapped[float] = mapped_column(Float, default=0)

    # Owner contactability (from the source exports; e.g. Yardi has a phone for
    # nearly every owner). Skip-trace APIs can fill the email gap later.
    owner_contact: Mapped[str] = mapped_column(String(160), default="")
    owner_phone: Mapped[str] = mapped_column(String(40), default="")
    owner_email: Mapped[str] = mapped_column(String(160), default="")
    owner_website: Mapped[str] = mapped_column(String(200), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    score: Mapped["OpportunityScore"] = relationship(
        back_populates="property", cascade="all, delete-orphan", uselist=False
    )
    pipeline: Mapped["Pipeline"] = relationship(
        back_populates="property", cascade="all, delete-orphan", uselist=False
    )


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), primary_key=True)
    acquisition_score: Mapped[float] = mapped_column(Float, index=True)
    fit_score: Mapped[float] = mapped_column(Float, index=True, default=0)
    motivation_score: Mapped[float] = mapped_column(Float, index=True, default=0)
    call_score: Mapped[float] = mapped_column(Float, index=True, default=0)
    hold_period: Mapped[float] = mapped_column(Float)
    rent_gap: Mapped[float] = mapped_column(Float)
    basis_gap: Mapped[float] = mapped_column(Float)
    ownership_type_score: Mapped[float] = mapped_column(Float)
    owner_distance_score: Mapped[float] = mapped_column(Float)
    contactability_score: Mapped[float] = mapped_column(Float)

    hold_period_score: Mapped[float] = mapped_column(Float, default=0)
    rent_gap_score: Mapped[float] = mapped_column(Float, default=0)
    vintage_score: Mapped[float] = mapped_column(Float, default=0)
    basis_gap_score: Mapped[float] = mapped_column(Float, default=0)
    units_score: Mapped[float] = mapped_column(Float, default=0)
    private_owner_score: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[str] = mapped_column(String(40), default="Monitor")
    potential_721_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    estimated_tax_deferral: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped[Property] = relationship(back_populates="score")


class Pipeline(Base):
    __tablename__ = "pipeline"

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), primary_key=True)
    stage: Mapped[str] = mapped_column(String(40), index=True, default="Identified")
    notes: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped[Property] = relationship(back_populates="pipeline")
