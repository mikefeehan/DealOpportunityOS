import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT_DIR / "opportunityos.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the initial schema. Because this app uses create_all (no
# Alembic), existing local SQLite databases won't pick up new columns. This
# lightweight check adds any missing columns in-place so the dashboard always
# loads without forcing the user to delete opportunityos.db.
_ADDED_PROPERTY_COLUMNS = {
    "data_status": "VARCHAR(40) DEFAULT 'seeded_fallback'",
    "match_status": "VARCHAR(40) DEFAULT 'no_match'",
    "source_url": "VARCHAR(400) DEFAULT ''",
    "source_name": "VARCHAR(160) DEFAULT ''",
    "match_confidence": "FLOAT DEFAULT 0",
    "matched_address": "VARCHAR(255) DEFAULT ''",
    "last_verified_at": "DATETIME",
    "avg_unit_sf": "INTEGER DEFAULT 0",
    "address_key": "VARCHAR(160) DEFAULT ''",
    "market": "VARCHAR(120) DEFAULT 'Tucson, AZ'",
    "sources": "VARCHAR(255) DEFAULT ''",
    "star_rating": "FLOAT DEFAULT 0",
    "building_class": "VARCHAR(8) DEFAULT ''",
    "location_rating": "VARCHAR(16) DEFAULT ''",
    "cap_rate": "FLOAT DEFAULT 0",
    "vacancy": "FLOAT DEFAULT 0",
    "for_sale": "BOOLEAN DEFAULT 0",
    "for_sale_price": "FLOAT DEFAULT 0",
    "price_per_unit": "FLOAT DEFAULT 0",
    "last_sale_price": "FLOAT DEFAULT 0",
    "affordable": "BOOLEAN DEFAULT 0",
    "affordable_type": "VARCHAR(48) DEFAULT ''",
    "loan_maturity_year": "INTEGER DEFAULT 0",
    "interest_rate": "FLOAT DEFAULT 0",
    "loan_amount": "FLOAT DEFAULT 0",
    "year_renovated": "INTEGER DEFAULT 0",
    "effective_rent": "FLOAT DEFAULT 0",
    "owner_contact": "VARCHAR(160) DEFAULT ''",
    "owner_phone": "VARCHAR(40) DEFAULT ''",
    "owner_email": "VARCHAR(160) DEFAULT ''",
    "owner_website": "VARCHAR(200) DEFAULT ''",
    "manager_phone": "VARCHAR(40) DEFAULT ''",
}


def ensure_runtime_columns() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "properties" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("properties")}
    missing = {name: ddl for name, ddl in _ADDED_PROPERTY_COLUMNS.items() if name not in existing}
    if not missing:
        return
    with engine.begin() as conn:
        for name, ddl in missing.items():
            conn.execute(text(f"ALTER TABLE properties ADD COLUMN {name} {ddl}"))

