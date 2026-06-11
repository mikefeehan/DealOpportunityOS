# CLAUDE.md

## Project

OpportunityOS - Tucson Pilot for InTrust Property Group.

Workspace path:

`C:\Users\mikef\OneDrive\Documents\Rent Delta Deal Finder`

This is an internal acquisition intelligence platform. It is not a public SaaS product, not a CRM, and not a rent comp platform. The core job is to answer:

> Who are the 25 apartment owners in Tucson that InTrust should call this week?

The product should think like an acquisitions associate. Owners are the leads. Properties are containers.

## Current Repo State

Local Git repo exists on branch `main`.

Initial app commit:

`4d254d8 Initial OpportunityOS Tucson pilot`

After this handoff file is committed, latest commit should include `CLAUDE.md`.

Ignored local runtime files:

- `.venv/`
- `opportunityos.db`
- `opportunityos_scan.log`
- `frontend/node_modules/`
- `frontend/.next/`
- `.playwright-mcp/`

Do not commit credentials, cookies, SQLite runtime data, logs, or browser session storage.

## Important Truth About Data

The current app is functional, but the visible "deals" are seeded fallback/demo records.

They are not verified real acquisition opportunities.

The app now displays a provenance banner when fallback data is active:

`Data mode: Seeded fallback. Live records: 0. Fallback records: 30. Seeded fallback records are pilot/demo intelligence and are not verified real acquisition opportunities.`

Current live scan status:

- Pima/Tucson public parcel endpoints are reachable.
- They returned parcel records.
- They did not expose enough reliable unit/building-size data to safely identify 50+ or 75+ unit multifamily records.
- Apartments.com returned 403.
- Zillow/RentCafe pages were reachable only as market reference pages, not reliable structured acquisition inventory.
- Fallback remains active until a verified apartment universe source is connected.

Do not imply the current Top Owners list is real. It proves the workflow and scoring engine.

## Tech Stack

Backend:

- FastAPI
- SQLite
- SQLAlchemy
- ReportLab for PDF
- BeautifulSoup for HTML extraction attempts

Frontend:

- Next.js 16
- TypeScript
- Tailwind
- shadcn-style local UI primitives
- lucide-react icons

OpenAI:

- Uses `OPENAI_API_KEY` if available.
- Used only for narrative output:
  - Why Now summaries
  - Recommended outreach angles
  - Owner intelligence summaries
  - Property summaries
  - AI call prep
- Do not use OpenAI for scoring, ranking, filtering, or data collection.
- If the key is missing or OpenAI fails, rule-based call prep is used.

## Run Commands

From repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Backend:

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev -- -p 3001
```

Use port `3001` because another local app was already using `3000` during the build.

Open:

`http://localhost:3001`

Backend health:

`http://127.0.0.1:8000/api/health`

Convenience script:

```powershell
.\scripts\start-dev.ps1
```

Note: that script starts the frontend default dev command from package scripts. If port 3000 is occupied, use the manual frontend command with `-p 3001`.

## Verification Already Done

The following passed:

```powershell
.\.venv\Scripts\python -m compileall backend
cd frontend
npm run build
npm audit --omit=dev
```

Frontend audit returned 0 vulnerabilities after upgrading to Next 16 and overriding/pinning PostCSS to `8.5.10`.

Browser verification was done against:

`http://localhost:3001`

Checked:

- Homepage loads
- Provenance banner appears
- Opportunity Finder route loads
- Property detail route loads
- Pipeline route loads
- CSV and PDF export links are present

## Backend Structure

Main app:

- `backend/app/main.py`

Database:

- `backend/app/database.py`

Models:

- `backend/app/models.py`

Tables:

- `properties`
- `opportunity_scores`
- `pipeline`

Services:

- `backend/app/services/scoring.py`
  - deterministic scoring engine
  - acquisition score
  - fit score
  - motivation score
  - call score
  - 721 candidate logic
  - Ignore / Monitor / Call Owner recommendation

- `backend/app/services/ranking.py`
  - owner aggregation
  - ranked property list
  - ranked owner list
  - market summary
  - Today's Call List
  - provenance summary

- `backend/app/services/scanner.py`
  - Tucson scan service
  - public Pima/Tucson parcel attempts
  - configured authorized source URL attempts
  - seeded fallback load
  - scan logging

- `backend/app/services/seed_data.py`
  - seeded Tucson demo/fallback multifamily records

- `backend/app/services/ai_insights.py`
  - OpenAI call prep
  - rule-based fallback call prep

- `backend/app/services/exports.py`
  - CSV export
  - Today's Call List PDF

- `backend/app/services/importer.py` (added)
  - Real Universe importer: parse CSV/XLSX, flexible column mapping
  - Pima parcel match attempt, parcel-match confidence
  - upsert as `live_authorized` with `match_status` of `needs_review` / `no_match`

- `backend/app/services/review.py` (added)
  - parcel-match review queue
  - confirm (-> `verified`) / reject (delete) actions

## API Endpoints

Health:

- `GET /api/health`

Scan:

- `POST /api/scan/tucson`

Summary:

- `GET /api/market/summary`

Call list:

- `GET /api/today-call-list`

Properties:

- `GET /api/opportunities`
- `GET /api/properties/{property_id}`

Owners:

- `GET /api/owners`
- `GET /api/owners/{owner_name}`

Pipeline:

- `GET /api/pipeline`
- `PATCH /api/pipeline/{property_id}`

Exports:

- `GET /api/export/csv`
- `GET /api/export/today-call-list.pdf`

AI:

- `POST /api/ai/call-prep`

Real Universe import + parcel-match review (added):

- `POST /api/import/universe` (multipart: `file` = .csv/.xlsx, `source_name` = label)
- `GET /api/review-queue?include_verified=false`
- `POST /api/review/{property_id}/confirm` (promote to `verified`)
- `POST /api/review/{property_id}/reject` (delete imported record)

Data scope (added to opportunities / owners / today-call-list):

- `data_scope=verified` = verified live records only
- `data_scope=all` = everything incl. seeded demo fallback
- omitted / `auto` = verified live if any exist, else fallback (dashboard never empty)

## Frontend Structure

Root:

- `frontend/src/app/layout.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`

Pages:

- `frontend/src/app/page.tsx`
  - Top Owners To Call homepage

- `frontend/src/app/command-center/page.tsx`
  - Market Command Center

- `frontend/src/app/opportunities/page.tsx`
  - Opportunity Finder

- `frontend/src/app/owners/page.tsx`
  - Owner Intelligence list

- `frontend/src/app/owners/[ownerName]/page.tsx`
  - Owner profile detail

- `frontend/src/app/properties/[id]/page.tsx`
  - Property detail

- `frontend/src/app/pipeline/page.tsx`
  - Pipeline board

- `frontend/src/app/review/page.tsx`
  - Import & Review queue (Real Universe importer + parcel-match confirm/reject)

Shared shell:

- `frontend/src/components/app-shell.tsx`

API client:

- `frontend/src/lib/api.ts`

Types:

- `frontend/src/lib/types.ts`

Fallback client-side preview:

- `frontend/src/lib/fallback.ts`

Local shadcn-style UI:

- `frontend/src/components/ui/*`

## Scoring Logic

The app creates three main operational scores:

Fit Score:

> How attractive is the asset to InTrust?

Signals:

- Unit count, especially 75+ units
- Built 1970-2015
- Rent upside
- Basis gap
- Target ownership geography
- Penalizes new/luxury assets

Motivation Score:

> How likely is the owner to engage in a conversation?

Signals:

- Long hold period
- Private/family/trust/LLC ownership
- Out-of-state owner
- Contactability
- 721 candidate signals
- Penalizes recent trades and institutional ownership

Call Score:

`Call Score = Fit Score * 50% + Motivation Score * 50%`

Outcomes:

- `Call Owner`
- `Monitor`
- `Ignore`

The threshold for `Call Owner` was tightened so only high-conviction opportunities get flagged. Do not loosen this casually.

## 721 Candidate Logic

Potential 721 candidate signals:

- Held more than 15 years
- Significant embedded gain / basis gap
- Private ownership
- Individual, family, trust, LLC, LP, or partnership ownership

The app estimates tax deferral from the modeled embedded gain.

This is directional only. It is not tax advice.

## InTrust Mode

InTrust Mode is a special filter.

Default criteria:

- 75+ units
- Built 1970-2015
- Held more than 10 years
- Private ownership
- Non-institutional ownership
- Arizona, California, or Nevada owner location

Purpose:

Surface Heritage Housing Fund-style acquisition targets.

## Data Source Reality And Best Next Step

The user does not want to pay for APIs.

Yardi, RealPage, and HelloData are private systems that require user ID/password. Do not ask the user to paste credentials into chat. Do not commit credentials. Do not store passwords in repo files.

Best no-paid-API paths, in order:

1. Manual export from a tool the user already has access to.
   - Best if HelloData/Yardi/RealPage can export CSV/XLSX from the UI.
   - Then build a file importer.
   - This is cleanest, least fragile, and avoids browser automation issues.

2. Authorized browser-session automation.
   - User logs in locally.
   - Save local browser/session state outside Git.
   - Automation reads/searches Tucson results.
   - Works only if there is no MFA/CAPTCHA/SSO blocker during automated runs.

3. Public web and parcel enrichment.
   - Harder and less reliable.
   - Good as supplement, not primary source.

4. One-time manually researched Tucson universe.
   - Create verified seed from real public research.
   - Then let app enrich/score daily.

Recommended next build:

Build an "Import Real Universe" workflow before trying deeper scraping:

- Accept CSV/XLSX from HelloData/Yardi/RealPage manual export.
- Required columns:
  - property name
  - address
  - units
  - year built
  - current/asking rent if available
  - source
- Normalize addresses.
- Match to Pima parcel records.
- Store parcel match confidence:
  - `Verified`
  - `Needs Review`
  - `No Match`
- Only `Verified` records should enter the real call list.

This gives the user real deals fastest without paying for APIs.

## Current Authorized Source Hooks

Files:

- `.env.example`
- `data/source_urls.example.txt`
- `backend/app/services/scanner.py`

Supported local env placeholders:

```text
ACQUISITION_SOURCE_URLS=
YARDI_COOKIE=
REALPAGE_COOKIE=
HELLODATA_COOKIE=
YARDI_LOGIN_URL=
YARDI_USERNAME=
YARDI_PASSWORD=
REALPAGE_LOGIN_URL=
REALPAGE_USERNAME=
REALPAGE_PASSWORD=
HELLODATA_LOGIN_URL=
HELLODATA_USERNAME=
HELLODATA_PASSWORD=
```

These are placeholders only. Real values must go in a local `.env` or secure local session file that is ignored by Git.

Current scanner can:

- Read URLs from `ACQUISITION_SOURCE_URLS`
- Read URLs from `data/source_urls.txt`
- Send source-specific cookies if provided
- Parse simple HTML/JSON-LD property pages
- Enrich by Pima parcel address lookup

Limitations:

- It does not yet perform full form login.
- It does not yet use Playwright to navigate private dashboards.
- It does not yet import CSV/XLSX.
- It does not yet persist parcel match confidence fields in the database.

## Suggested Next Implementation Tasks

Task 1: Add Real Universe Importer — DONE

- `POST /api/import/universe` accepts `.csv` / `.xlsx` (`backend/app/services/importer.py`).
- Standard-lib CSV + `openpyxl` for XLSX (no pandas). `python-multipart` for upload.
- Flexible header mapping in `COLUMN_ALIASES` (property name / address / units required-ish).
- Upserts by Pima parcel ID when matched, else a deterministic synthetic `IMP-<hash>` id.
- Template for the user to fill: `data/universe_import_template.csv`.
- Note: manual imports without a sale year default `last_sale_year` to `DEFAULT_LAST_SALE_YEAR`
  (2012) — a neutral placeholder so motivation scoring isn't overstated. Enrich later.

Task 2: Add Parcel Match Confidence — DONE

- New `properties` columns (in `models.py`): `data_status`, `match_status`, `source_url`,
  `source_name`, `match_confidence`, `matched_address`, `last_verified_at`.
- Because there is no Alembic, `database.ensure_runtime_columns()` runs on startup and
  `ALTER TABLE`s any missing columns into an existing SQLite db (no need to delete the db).

Task 3: Add Review Queue Page — DONE

- `/review` (`frontend/src/components/review-page.tsx`): upload panel + review table.
- `GET /api/review-queue`, `POST /api/review/{id}/confirm`, `POST /api/review/{id}/reject`
  (`backend/app/services/review.py`). Confirm -> `verified`; reject deletes the record.
- `no_match` rows can still be "Verify anyway" (manual override) so real deals that don't
  auto-match aren't dead-ended.

Task 4: Hide Fallback From Real Call List — DONE

- `data_scope` param on opportunities/owners/today-call-list (`verified` / `all` / auto).
- Homepage toggle "Verified Live Only" vs "Include Demo Fallback"; defaults to verified once
  any verified live record exists, else falls back so the dashboard is never empty.
- Provenance banner now counts `verified_live_records` / `needs_review_records` by
  `data_status` instead of matching the source string.

Task 5: Optional Browser Automation

If manual export is unavailable:

- Use Playwright.
- User logs into HelloData/Yardi/RealPage manually.
- Save storage state locally outside Git.
- Build source-specific extraction adapters.
- Keep selectors in separate adapter files.

Do this one source at a time. Start with HelloData if available because it is closest to the missing inventory/rent layer.

## User Preferences And Constraints

The user wants:

- Tucson only
- No paid APIs
- Owner-first acquisition engine
- Not a CRM
- Not a rent comp platform
- Not a SaaS product
- No dead buttons
- Dashboard must always load
- Real owner call list as soon as data is verified

The user is asking direct practical questions. Be clear when something is demo/fallback versus real.

Do not overpromise private-site automation. Say:

- It can often be automated with an authorized session.
- It may fail with MFA, CAPTCHA, SSO, bot blocking, or terms restrictions.
- Best first option is manual export if available.

## Current Local Servers

At the time this handoff was written:

- Backend was started on `127.0.0.1:8000`
- Frontend was started on `localhost:3001`

If the app is not reachable, restart with the commands above.

## Known Issues / Caveats

1. Current database schema has no full migration system.
   - It uses SQLAlchemy `create_all` for table creation.
   - `database.ensure_runtime_columns()` adds known new columns to an existing SQLite db on
     startup (lightweight `ALTER TABLE`), so the provenance/match columns land without
     deleting `opportunityos.db`. For larger schema changes, still consider Alembic.

2. Seed data is demo-like.
   - It is designed to exercise scoring and owner grouping.
   - Do not represent it as verified real deals.

3. The scanner's public source import is conservative.
   - It refuses to import parcels without reliable 50+ unit evidence.
   - This is intentional.

4. `scripts/start-dev.ps1` may start frontend on port 3000.
   - Use manual command with `-p 3001` if needed.

5. OpenAI model env default is `gpt-5.5` in `.env.example`.
   - If unavailable in the user's account, set `OPENAI_MODEL` to an available current model.
   - The app falls back to rule-based prep if OpenAI fails.

## What To Say To The User Next

If the user asks "what do I do now?", recommend this:

1. Open HelloData/Yardi/RealPage.
2. Check whether Tucson multifamily results can be exported to CSV/XLSX.
3. If yes, download one sample export.
4. Put it in the workspace, or tell the assistant the file path.
5. Build/import that file into the app and match to Pima parcels.

If no export exists:

1. Ask the user to log in locally.
2. Use an authorized browser session.
3. Build one adapter for one source, starting with HelloData.

## Quick Health Check Commands

```powershell
git status --short --branch
.\.venv\Scripts\python -m compileall backend
cd frontend
npm run build
npm audit --omit=dev
```

API smoke test:

```powershell
@'
import requests
for path in ['/api/health', '/api/market/summary', '/api/today-call-list']:
    r = requests.get('http://127.0.0.1:8000' + path, timeout=10)
    print(path, r.status_code, len(r.text))
'@ | .\.venv\Scripts\python -
```

Scan smoke test:

```powershell
@'
import requests, json
r = requests.post('http://127.0.0.1:8000/api/scan/tucson', timeout=45)
print(r.status_code)
print(json.dumps(r.json(), indent=2)[:4000])
'@ | .\.venv\Scripts\python -
```

Expected current scan result:

- `fallback_active: true`
- `live_records_imported: 0`
- `seeded_records_loaded: 30`

That is expected until a real apartment universe source is imported.
