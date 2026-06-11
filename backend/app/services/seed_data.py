from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import OpportunityScore, Pipeline, Property
from backend.app.services.scoring import calculate_score


SEEDED_PROPERTIES = [
    {
        "parcel_id": "SEED-TUC-0001",
        "name": "Palo Verde Vista",
        "address": "1485 E Fort Lowell Rd, Tucson, AZ 85719",
        "units": 124,
        "year_built": 1973,
        "assessed_value": 8950000,
        "owner_name": "Desert Ridge Multifamily LLC",
        "mailing_address": "433 N Camden Dr Ste 640, Beverly Hills, CA 90210",
        "latitude": 32.2654,
        "longitude": -110.9482,
        "submarket": "Central Tucson",
        "owner_city": "Beverly Hills",
        "owner_state": "CA",
        "last_sale_year": 1999,
        "average_rent": 965,
        "market_rent": 1295,
    },
    {
        "parcel_id": "SEED-TUC-0002",
        "name": "Campbell Terrace",
        "address": "3025 N Campbell Ave, Tucson, AZ 85719",
        "units": 88,
        "year_built": 1968,
        "assessed_value": 6120000,
        "owner_name": "Old Pueblo Terrace Partners LP",
        "mailing_address": "2525 E Broadway Blvd Ste 200, Tucson, AZ 85716",
        "latitude": 32.2628,
        "longitude": -110.9438,
        "submarket": "Campbell Corridor",
        "owner_city": "Tucson",
        "owner_state": "AZ",
        "last_sale_year": 1994,
        "average_rent": 910,
        "market_rent": 1235,
    },
    {
        "parcel_id": "SEED-TUC-0003",
        "name": "Oracle Palms",
        "address": "3601 N Oracle Rd, Tucson, AZ 85705",
        "units": 156,
        "year_built": 1977,
        "assessed_value": 11150000,
        "owner_name": "Sonoran Value Add Holdings LLC",
        "mailing_address": "1999 Avenue of the Stars Ste 1100, Los Angeles, CA 90067",
        "latitude": 32.2734,
        "longitude": -110.9786,
        "submarket": "North Oracle",
        "owner_city": "Los Angeles",
        "owner_state": "CA",
        "last_sale_year": 2001,
        "average_rent": 980,
        "market_rent": 1325,
    },
    {
        "parcel_id": "SEED-TUC-0004",
        "name": "Pantano Crossing",
        "address": "8465 E Speedway Blvd, Tucson, AZ 85710",
        "units": 212,
        "year_built": 1984,
        "assessed_value": 17300000,
        "owner_name": "Pantano Crossing Family Trust",
        "mailing_address": "7350 E Broadway Blvd Ste 202, Tucson, AZ 85710",
        "latitude": 32.2358,
        "longitude": -110.8114,
        "submarket": "East Tucson",
        "owner_city": "Tucson",
        "owner_state": "AZ",
        "last_sale_year": 1997,
        "average_rent": 1040,
        "market_rent": 1375,
    },
    {
        "parcel_id": "SEED-TUC-0005",
        "name": "22nd Street Flats",
        "address": "1258 S Craycroft Rd, Tucson, AZ 85711",
        "units": 72,
        "year_built": 1965,
        "assessed_value": 4760000,
        "owner_name": "Craycroft Income Properties LLC",
        "mailing_address": "6900 E Camelback Rd Ste 730, Scottsdale, AZ 85251",
        "latitude": 32.2069,
        "longitude": -110.8756,
        "submarket": "Midtown East",
        "owner_city": "Scottsdale",
        "owner_state": "AZ",
        "last_sale_year": 1992,
        "average_rent": 850,
        "market_rent": 1180,
    },
    {
        "parcel_id": "SEED-TUC-0006",
        "name": "River Road Garden",
        "address": "4101 E River Rd, Tucson, AZ 85718",
        "units": 96,
        "year_built": 1979,
        "assessed_value": 7820000,
        "owner_name": "Catalina Garden Apartments LLC",
        "mailing_address": "3333 Michelson Dr Ste 550, Irvine, CA 92612",
        "latitude": 32.2868,
        "longitude": -110.9054,
        "submarket": "Foothills",
        "owner_city": "Irvine",
        "owner_state": "CA",
        "last_sale_year": 2000,
        "average_rent": 1090,
        "market_rent": 1435,
    },
    {
        "parcel_id": "SEED-TUC-0007",
        "name": "Valencia Court",
        "address": "5150 S 12th Ave, Tucson, AZ 85706",
        "units": 132,
        "year_built": 1981,
        "assessed_value": 7350000,
        "owner_name": "Borderland Workforce Housing LP",
        "mailing_address": "101 N 1st Ave Ste 2400, Phoenix, AZ 85003",
        "latitude": 32.1618,
        "longitude": -110.9784,
        "submarket": "South Tucson",
        "owner_city": "Phoenix",
        "owner_state": "AZ",
        "last_sale_year": 1996,
        "average_rent": 790,
        "market_rent": 1125,
    },
    {
        "parcel_id": "SEED-TUC-0008",
        "name": "Speedway Commons",
        "address": "4555 E Speedway Blvd, Tucson, AZ 85712",
        "units": 118,
        "year_built": 1972,
        "assessed_value": 9050000,
        "owner_name": "Speedway Commons Owner LLC",
        "mailing_address": "1717 McKinney Ave Ste 1900, Dallas, TX 75202",
        "latitude": 32.2357,
        "longitude": -110.8959,
        "submarket": "Central East",
        "owner_city": "Dallas",
        "owner_state": "TX",
        "last_sale_year": 2005,
        "average_rent": 990,
        "market_rent": 1305,
    },
    {
        "parcel_id": "SEED-TUC-0009",
        "name": "Grant Park Villas",
        "address": "2802 E Grant Rd, Tucson, AZ 85716",
        "units": 64,
        "year_built": 1962,
        "assessed_value": 3920000,
        "owner_name": "Grant Park Villas LLC",
        "mailing_address": "6222 N Central Ave Ste 500, Phoenix, AZ 85012",
        "latitude": 32.2511,
        "longitude": -110.9309,
        "submarket": "Central Tucson",
        "owner_city": "Phoenix",
        "owner_state": "AZ",
        "last_sale_year": 1988,
        "average_rent": 825,
        "market_rent": 1165,
    },
    {
        "parcel_id": "SEED-TUC-0010",
        "name": "Kolb Landing",
        "address": "7050 E Golf Links Rd, Tucson, AZ 85730",
        "units": 180,
        "year_built": 1986,
        "assessed_value": 12900000,
        "owner_name": "Kolb Landing Partners LLC",
        "mailing_address": "1980 Festival Plaza Dr Ste 650, Las Vegas, NV 89135",
        "latitude": 32.1908,
        "longitude": -110.8417,
        "submarket": "Southeast Tucson",
        "owner_city": "Las Vegas",
        "owner_state": "NV",
        "last_sale_year": 2004,
        "average_rent": 1015,
        "market_rent": 1320,
    },
    {
        "parcel_id": "SEED-TUC-0011",
        "name": "Stone Avenue Lofts",
        "address": "240 N Stone Ave, Tucson, AZ 85701",
        "units": 58,
        "year_built": 1998,
        "assessed_value": 6900000,
        "owner_name": "Stone Avenue Residential LLC",
        "mailing_address": "1 E Washington St Ste 1800, Phoenix, AZ 85004",
        "latitude": 32.2246,
        "longitude": -110.9721,
        "submarket": "Downtown",
        "owner_city": "Phoenix",
        "owner_state": "AZ",
        "last_sale_year": 2007,
        "average_rent": 1185,
        "market_rent": 1430,
    },
    {
        "parcel_id": "SEED-TUC-0012",
        "name": "Wilmot Village",
        "address": "6620 E Broadway Blvd, Tucson, AZ 85710",
        "units": 144,
        "year_built": 1975,
        "assessed_value": 10850000,
        "owner_name": "Wilmot Village Holdings LLC",
        "mailing_address": "2029 Century Park E Ste 400, Los Angeles, CA 90067",
        "latitude": 32.2211,
        "longitude": -110.8522,
        "submarket": "East Broadway",
        "owner_city": "Los Angeles",
        "owner_state": "CA",
        "last_sale_year": 2002,
        "average_rent": 970,
        "market_rent": 1310,
    },
    {
        "parcel_id": "SEED-TUC-0013",
        "name": "Dodge Flower Apartments",
        "address": "3301 E Flower St, Tucson, AZ 85716",
        "units": 54,
        "year_built": 1969,
        "assessed_value": 3450000,
        "owner_name": "Flower Street Apartments LLC",
        "mailing_address": "7447 E Indian School Rd Ste 205, Scottsdale, AZ 85251",
        "latitude": 32.2529,
        "longitude": -110.9202,
        "submarket": "Central Tucson",
        "owner_city": "Scottsdale",
        "owner_state": "AZ",
        "last_sale_year": 1991,
        "average_rent": 815,
        "market_rent": 1140,
    },
    {
        "parcel_id": "SEED-TUC-0014",
        "name": "Ajo Way Residences",
        "address": "1640 W Ajo Way, Tucson, AZ 85713",
        "units": 102,
        "year_built": 1980,
        "assessed_value": 5850000,
        "owner_name": "Ajo Workforce Residential LP",
        "mailing_address": "5808 Lake Washington Blvd NE Ste 300, Kirkland, WA 98033",
        "latitude": 32.1771,
        "longitude": -111.0007,
        "submarket": "Southwest Tucson",
        "owner_city": "Kirkland",
        "owner_state": "WA",
        "last_sale_year": 2003,
        "average_rent": 775,
        "market_rent": 1115,
    },
    {
        "parcel_id": "SEED-TUC-0015",
        "name": "Broadway Swan Commons",
        "address": "4710 E Broadway Blvd, Tucson, AZ 85711",
        "units": 76,
        "year_built": 1971,
        "assessed_value": 5480000,
        "owner_name": "Swan Broadway Income LLC",
        "mailing_address": "3200 N Central Ave Ste 1150, Phoenix, AZ 85012",
        "latitude": 32.2212,
        "longitude": -110.8923,
        "submarket": "Midtown East",
        "owner_city": "Phoenix",
        "owner_state": "AZ",
        "last_sale_year": 1998,
        "average_rent": 900,
        "market_rent": 1225,
    },
    {
        "parcel_id": "SEED-TUC-0016",
        "name": "Tanque Verde Station",
        "address": "7601 E Tanque Verde Rd, Tucson, AZ 85715",
        "units": 168,
        "year_built": 1991,
        "assessed_value": 15100000,
        "owner_name": "Tanque Verde Station LLC",
        "mailing_address": "500 N Akard St Ste 3200, Dallas, TX 75201",
        "latitude": 32.2517,
        "longitude": -110.8281,
        "submarket": "Northeast Tucson",
        "owner_city": "Dallas",
        "owner_state": "TX",
        "last_sale_year": 2006,
        "average_rent": 1135,
        "market_rent": 1410,
    },
    {
        "parcel_id": "SEED-TUC-0017",
        "name": "Euclid University Courts",
        "address": "1125 N Euclid Ave, Tucson, AZ 85719",
        "units": 92,
        "year_built": 1964,
        "assessed_value": 7100000,
        "owner_name": "University Courts Partners LLC",
        "mailing_address": "8500 E Raintree Dr Ste 250, Scottsdale, AZ 85260",
        "latitude": 32.2367,
        "longitude": -110.9597,
        "submarket": "University",
        "owner_city": "Scottsdale",
        "owner_state": "AZ",
        "last_sale_year": 1990,
        "average_rent": 1045,
        "market_rent": 1395,
    },
    {
        "parcel_id": "SEED-TUC-0018",
        "name": "Prince Road Commons",
        "address": "1717 E Prince Rd, Tucson, AZ 85719",
        "units": 108,
        "year_built": 1978,
        "assessed_value": 8080000,
        "owner_name": "Prince Road Commons LLC",
        "mailing_address": "100 Wilshire Blvd Ste 700, Santa Monica, CA 90401",
        "latitude": 32.2724,
        "longitude": -110.9469,
        "submarket": "North Central",
        "owner_city": "Santa Monica",
        "owner_state": "CA",
        "last_sale_year": 2001,
        "average_rent": 940,
        "market_rent": 1275,
    },
    {
        "parcel_id": "SEED-TUC-0019",
        "name": "Irvington Park",
        "address": "3450 E Irvington Rd, Tucson, AZ 85714",
        "units": 136,
        "year_built": 1983,
        "assessed_value": 7900000,
        "owner_name": "Irvington Park Estates LLC",
        "mailing_address": "2390 E Camelback Rd Ste 410, Phoenix, AZ 85016",
        "latitude": 32.1626,
        "longitude": -110.9187,
        "submarket": "South Tucson",
        "owner_city": "Phoenix",
        "owner_state": "AZ",
        "last_sale_year": 1995,
        "average_rent": 805,
        "market_rent": 1145,
    },
    {
        "parcel_id": "SEED-TUC-0020",
        "name": "Rillito Bend",
        "address": "3900 N 1st Ave, Tucson, AZ 85719",
        "units": 84,
        "year_built": 1976,
        "assessed_value": 6260000,
        "owner_name": "Rillito Bend Apartments LLC",
        "mailing_address": "650 California St Ste 2800, San Francisco, CA 94108",
        "latitude": 32.2786,
        "longitude": -110.9612,
        "submarket": "North Central",
        "owner_city": "San Francisco",
        "owner_state": "CA",
        "last_sale_year": 2000,
        "average_rent": 930,
        "market_rent": 1250,
    },
    {
        "parcel_id": "SEED-TUC-0021",
        "name": "Stella Wilmot Homes",
        "address": "6701 E Stella Rd, Tucson, AZ 85730",
        "units": 120,
        "year_built": 1988,
        "assessed_value": 8720000,
        "owner_name": "Stella Wilmot Housing LLC",
        "mailing_address": "2141 E Highland Ave Ste 250, Phoenix, AZ 85016",
        "latitude": 32.1861,
        "longitude": -110.8499,
        "submarket": "Southeast Tucson",
        "owner_city": "Phoenix",
        "owner_state": "AZ",
        "last_sale_year": 2008,
        "average_rent": 960,
        "market_rent": 1220,
    },
    {
        "parcel_id": "SEED-TUC-0022",
        "name": "Silverbell Mesa",
        "address": "1980 W Speedway Blvd, Tucson, AZ 85745",
        "units": 150,
        "year_built": 1985,
        "assessed_value": 10250000,
        "owner_name": "Silverbell Mesa Residential LLC",
        "mailing_address": "1900 16th St Ste 950, Denver, CO 80202",
        "latitude": 32.2355,
        "longitude": -111.0101,
        "submarket": "West Tucson",
        "owner_city": "Denver",
        "owner_state": "CO",
        "last_sale_year": 2002,
        "average_rent": 980,
        "market_rent": 1295,
    },
    {
        "parcel_id": "SEED-TUC-0023",
        "name": "Country Club Gardens",
        "address": "2600 N Country Club Rd, Tucson, AZ 85716",
        "units": 66,
        "year_built": 1961,
        "assessed_value": 4075000,
        "owner_name": "Country Club Garden Estate",
        "mailing_address": "6053 E Grant Rd, Tucson, AZ 85712",
        "latitude": 32.2549,
        "longitude": -110.9262,
        "submarket": "Central Tucson",
        "owner_city": "Tucson",
        "owner_state": "AZ",
        "last_sale_year": 1987,
        "average_rent": 800,
        "market_rent": 1160,
    },
    {
        "parcel_id": "SEED-TUC-0024",
        "name": "Broadmoor Wash",
        "address": "3425 E 29th St, Tucson, AZ 85713",
        "units": 80,
        "year_built": 1970,
        "assessed_value": 4890000,
        "owner_name": "Broadmoor Wash Apartments LLC",
        "mailing_address": "401 Congress Ave Ste 1540, Austin, TX 78701",
        "latitude": 32.1996,
        "longitude": -110.9195,
        "submarket": "Central South",
        "owner_city": "Austin",
        "owner_state": "TX",
        "last_sale_year": 1999,
        "average_rent": 825,
        "market_rent": 1175,
    },
    {
        "parcel_id": "SEED-TUC-0025",
        "name": "Alvernon Square",
        "address": "2110 N Alvernon Way, Tucson, AZ 85712",
        "units": 104,
        "year_built": 1974,
        "assessed_value": 7000000,
        "owner_name": "Alvernon Square Partners LP",
        "mailing_address": "600 Montgomery St Ste 1200, San Francisco, CA 94111",
        "latitude": 32.2472,
        "longitude": -110.9096,
        "submarket": "Central East",
        "owner_city": "San Francisco",
        "owner_state": "CA",
        "last_sale_year": 2001,
        "average_rent": 910,
        "market_rent": 1245,
    },
    {
        "parcel_id": "SEED-TUC-0026",
        "name": "La Cholla Ridge",
        "address": "3700 N La Cholla Blvd, Tucson, AZ 85705",
        "units": 188,
        "year_built": 1993,
        "assessed_value": 16750000,
        "owner_name": "La Cholla Ridge Owner LLC",
        "mailing_address": "3753 Howard Hughes Pkwy Ste 200, Las Vegas, NV 89169",
        "latitude": 32.2731,
        "longitude": -111.0129,
        "submarket": "Northwest Tucson",
        "owner_city": "Las Vegas",
        "owner_state": "NV",
        "last_sale_year": 2009,
        "average_rent": 1110,
        "market_rent": 1375,
    },
    {
        "parcel_id": "SEED-TUC-0027",
        "name": "Mission Road Apartments",
        "address": "2550 S Mission Rd, Tucson, AZ 85713",
        "units": 94,
        "year_built": 1978,
        "assessed_value": 5120000,
        "owner_name": "Mission Road Apartments LLC",
        "mailing_address": "2000 E Rio Salado Pkwy Ste 1050, Tempe, AZ 85281",
        "latitude": 32.1923,
        "longitude": -111.0018,
        "submarket": "Southwest Tucson",
        "owner_city": "Tempe",
        "owner_state": "AZ",
        "last_sale_year": 1994,
        "average_rent": 760,
        "market_rent": 1100,
    },
    {
        "parcel_id": "SEED-TUC-0028",
        "name": "Rincon East Apartments",
        "address": "8100 E 22nd St, Tucson, AZ 85710",
        "units": 160,
        "year_built": 1982,
        "assessed_value": 11800000,
        "owner_name": "Rincon East Multifamily LLC",
        "mailing_address": "10900 NE 4th St Ste 2300, Bellevue, WA 98004",
        "latitude": 32.2069,
        "longitude": -110.8193,
        "submarket": "East Tucson",
        "owner_city": "Bellevue",
        "owner_state": "WA",
        "last_sale_year": 2005,
        "average_rent": 1020,
        "market_rent": 1340,
    },
    {
        "parcel_id": "SEED-TUC-0029",
        "name": "Mountain First Commons",
        "address": "3201 N 1st Ave, Tucson, AZ 85719",
        "units": 70,
        "year_built": 1967,
        "assessed_value": 4300000,
        "owner_name": "Desert Ridge Multifamily LLC",
        "mailing_address": "433 N Camden Dr Ste 640, Beverly Hills, CA 90210",
        "latitude": 32.2661,
        "longitude": -110.9611,
        "submarket": "North Central",
        "owner_city": "Beverly Hills",
        "owner_state": "CA",
        "last_sale_year": 1998,
        "average_rent": 845,
        "market_rent": 1210,
    },
    {
        "parcel_id": "SEED-TUC-0030",
        "name": "Broadway Pantano Village",
        "address": "7850 E Broadway Blvd, Tucson, AZ 85710",
        "units": 226,
        "year_built": 1987,
        "assessed_value": 18400000,
        "owner_name": "Broadway Pantano Village LLC",
        "mailing_address": "400 Capitol Mall Ste 1900, Sacramento, CA 95814",
        "latitude": 32.2211,
        "longitude": -110.8242,
        "submarket": "East Broadway",
        "owner_city": "Sacramento",
        "owner_state": "CA",
        "last_sale_year": 2004,
        "average_rent": 1065,
        "market_rent": 1370,
    },
]


# Fields where a newer source should overwrite an existing value (financials,
# ratings, physical facts). Everything else is fill-only (keep the first source),
# which preserves stable owner grouping and identity across merges.
_MERGE_OVERWRITE = {
    "star_rating", "building_class", "location_rating", "cap_rate", "vacancy", "for_sale",
    "for_sale_price", "price_per_unit", "last_sale_price", "affordable", "affordable_type",
    "loan_maturity_year", "year_renovated", "effective_rent", "market", "submarket",
    "year_built", "last_sale_year", "market_rent", "building_sqft", "property_type",
    "match_status", "match_confidence", "matched_address", "data_status",
}
_KEEP_IDENTITY = {"parcel_id", "address_key", "created_at", "sources"}


def _empty(value) -> bool:
    return value in (None, "", 0, 0.0, False)


def _merge_payload(existing: Property, payload: dict) -> None:
    for key, value in payload.items():
        if key in _KEEP_IDENTITY or _empty(value):
            continue
        if _empty(getattr(existing, key, None)) or key in _MERGE_OVERWRITE:
            setattr(existing, key, value)
    new_source = payload.get("sources") or payload.get("source_name")
    if new_source and new_source not in (existing.sources or ""):
        existing.sources = ", ".join(part for part in [existing.sources, new_source] if part)


def upsert_property(db: Session, payload: dict, merge: bool = False) -> Property:
    payload = {**payload}
    payload.setdefault("building_sqft", int((payload.get("units") or 0) * 875))
    existing = None
    address_key = payload.get("address_key")
    if address_key:
        existing = db.scalar(select(Property).where(Property.address_key == address_key))
    if not existing:
        existing = db.scalar(select(Property).where(Property.parcel_id == payload["parcel_id"]))
    if existing:
        if merge:
            _merge_payload(existing, payload)
        else:
            for key, value in payload.items():
                setattr(existing, key, value)
        prop = existing
    else:
        prop = Property(**payload)
        db.add(prop)
        db.flush()

    score = calculate_score(prop)
    if prop.score:
        score_row = prop.score
    else:
        score_row = OpportunityScore(property_id=prop.id)
        db.add(score_row)

    for key, value in score.__dict__.items():
        setattr(score_row, key, value)

    if not prop.pipeline:
        db.add(Pipeline(property_id=prop.id, stage="Identified", notes=""))

    # Flush so the score/pipeline are visible if the same property is upserted
    # again within an uncommitted batch (e.g. duplicate parcel ids in one import).
    db.flush()

    return prop


def dedupe_by_street(db: Session) -> int:
    """Merge same-site records that share street name + units + vintage.

    Catches duplicates the address key misses (house-number ranges, etc.) while
    staying conservative: it requires the same market, the same street-name key,
    the same unit count, and a build year within two years before merging.
    """
    from collections import defaultdict

    from backend.app.services.addresses import street_name_key

    rows = db.scalars(select(Property).where(Property.data_status != "seeded_fallback")).all()
    groups: dict[tuple, list[Property]] = defaultdict(list)
    for prop in rows:
        key = street_name_key(prop.address)
        if key and prop.units:
            groups[(prop.market, key, prop.units)].append(prop)

    removed = 0
    columns = [c.name for c in Property.__table__.columns if c.name != "id"]
    for members in groups.values():
        if len(members) < 2:
            continue
        # Sub-cluster by build year so genuinely different buildings on the same
        # street with the same unit count (different vintages) are NOT merged.
        members.sort(key=lambda p: p.year_built or 0)
        clusters: list[list[Property]] = []
        for prop in members:
            for cluster in clusters:
                if abs((prop.year_built or 0) - (cluster[0].year_built or 0)) <= 2:
                    cluster.append(prop)
                    break
            else:
                clusters.append([prop])
        for cluster in clusters:
            if len(cluster) < 2:
                continue
            cluster.sort(key=lambda p: (-len((p.sources or "").split(",")), p.id))
            canonical = cluster[0]
            for other in cluster[1:]:
                payload = {name: getattr(other, name) for name in columns}
                _merge_payload(canonical, payload)
                db.delete(other)
                removed += 1
    if removed:
        db.commit()
    return removed


def purge_seed_data(db: Session) -> int:
    """Delete all seeded demo records. Returns how many were removed."""
    rows = db.scalars(select(Property).where(Property.data_status == "seeded_fallback")).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return len(rows)


def has_live_data(db: Session) -> bool:
    return db.scalar(select(Property.id).where(Property.data_status != "seeded_fallback").limit(1)) is not None


def ensure_seed_data(db: Session) -> int:
    # Once real data exists, demo records are no longer needed: purge them and
    # don't re-seed. Demos only exist to keep a brand-new, empty install populated.
    if has_live_data(db):
        purge_seed_data(db)
        return 0
    inserted_or_updated = 0
    for payload in SEEDED_PROPERTIES:
        upsert_property(
            db,
            {
                **payload,
                "property_type": "Apartments",
                "source": "Seeded Tucson fallback",
                "data_status": "seeded_fallback",
                "match_status": "no_match",
                "source_name": "Seeded Tucson fallback",
            },
        )
        inserted_or_updated += 1
    db.commit()
    return inserted_or_updated
