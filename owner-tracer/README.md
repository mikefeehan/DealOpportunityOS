# owner-tracer

A free, semi-automated CLI for finding **Tucson / Pima County, AZ** multifamily
property-owner contact info. It automates the public-records lookups that can be
automated and hands you one-click search links for the parts that can't (people
search sites that block scraping).

```
python tracer.py "4444 E Grant Rd, Tucson, AZ"
python tracer.py --apn 116-05-009A
python tracer.py --csv list.csv          # bulk -> enriched_list.csv
python tracer.py "..." --open            # also open the contact links in a browser
python tracer.py "..." --no-prompt       # don't prompt for phone/email (still logs)
```

## Install

```
pip install -r requirements.txt
```

## Pipeline

1. **Pima County parcel lookup (automated).** Queries the Pima County Assessor
   county-wide parcel layer (PAREGION) over ArcGIS REST and returns owner /
   addressee, mailing address, APN, legal class/use, units and year built when
   present. Works by **address** (attribute LIKE on `SITE_ADDRESS`) or by
   **APN** (exact on `PARCEL`, tried with and without dashes). If it can't find a
   match it prints the manual Assessor search + parcel-viewer URLs.

2. **Entity resolution (Arizona).** If the owner name looks like an entity
   (LLC / LP / Trust / Inc / Partners / Holdings / …) it queries the free
   **OpenCorporates** API for the AZ entity and pulls members / statutory agent
   with their addresses, and always prints deep links to the **Arizona
   Corporation Commission** search. Individual owners skip straight to step 3.
   The mailing address is highlighted when it differs from the property address —
   that's frequently the principal's home or office.

3. **Contact search links (manual, one click).** For each principal it prints
   pre-filled **TruePeopleSearch**, **FastPeopleSearch**, **Google**, and
   **LinkedIn** search URLs. These sites block automated scraping, so the tool
   does not scrape them — it just builds the links (open them with `--open`).

4. **Logging.** Prompts you for any phone / email you found and appends a row to
   `tracker.csv` (date, address, APN, owner, principals, mailing, phone, email,
   status, notes). Bulk mode logs every row and also writes an enriched CSV.

## Endpoint notes & quirks

- **Pima parcel layer.** The PAREGION layer is hosted on the City of Tucson
  ArcGIS server (`mapdata.tucsonaz.gov/.../PropertyHousing/MapServer/17`) and
  covers City of Tucson **and** unincorporated Pima County. Useful fields:
  `PARCEL` (APN), `ADDRESSEE` (owner/taxpayer), `SITE_ADDRESS`, `MAIL1`–`MAIL5`
  (mailing), `USE_DESC` (legal class/use), `FCV` (full cash value), `YearBuilt`.
  If the endpoint moves, browse the ArcGIS REST directory at
  `https://gis.pima.gov/` or the Pima Geospatial Data Portal
  (`https://gisopendata.pima.gov/`) for the current parcel service and update
  `PIMA_PARCEL_LAYERS` at the top of `tracer.py`. Address matching is a `LIKE` on
  the first few address tokens, so very short or unusual addresses may need the
  APN path. Unit counts are often **not** exposed on the parcel layer — confirm
  on the Assessor record.

- **AZ Corporation Commission.** `ecorp.azcc.gov` (eCorp) was **decommissioned on
  2026-01-02**; the live portal is **Arizona Business Center**
  (`arizonabusinesscenter.azcc.gov/businesssearch`). It's a single-page app whose
  internal JSON API is not a stable/published endpoint, so this tool uses
  **OpenCorporates** for programmatic entity/officer data and deep-links the AZCC
  portal (and legacy eCorp) for manual confirmation. If/when AZCC publishes a
  stable API, wire it into `opencorporates_lookup`'s place.

- **OpenCorporates free tier** is rate-limited and may not return officer data for
  every entity (and out-of-state WY/DE shells won't be in the AZ jurisdiction —
  follow the printed AZCC/registered-agent trail in that case). The tool degrades
  gracefully: if there's no free match it still prints the AZCC search links.

- **People-search sites** (TruePeopleSearch / FastPeopleSearch) actively block
  bots and change markup often; scraping them is fragile and against their terms,
  so this tool intentionally only builds the search URLs for you to click.

## Output

`tracker.csv` accumulates every traced property so you build a reusable contact
sheet over time. Bulk runs also emit `enriched_<input>.csv`.

This tool only uses **free, public** data sources.
