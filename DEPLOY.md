# Deploying OpportunityOS

This is a **monorepo**: a Next.js frontend in `frontend/` and a FastAPI backend in
`backend/`. They deploy to two different places.

## Why the Vercel 404 happens

Vercel builds from the repo **root** by default, but the Next.js app lives in
`frontend/`. With no app at the root, Vercel has nothing to serve → `404 NOT_FOUND`.

## 1. Frontend → Vercel

1. Import this repo into Vercel.
2. **Project Settings → Build & Deployment → Root Directory → set to `frontend`.**
   This is the fix for the 404. Save and redeploy.
3. Vercel auto-detects Next.js (build `next build`, no other changes needed).
4. **Environment Variables** (Project Settings → Environment Variables):
   - `NEXT_PUBLIC_MAPBOX_TOKEN` — your Mapbox public token (for the maps).
   - `NEXT_PUBLIC_API_BASE` — the deployed backend URL (see step 2 below), e.g.
     `https://opportunityos-backend.onrender.com`. Without this the site loads but
     has no data.
5. Redeploy.

## 2. Backend → Render (or Railway / Fly)

The backend is **stateful** (SQLite + uploaded files + on-demand imports), so it is
not a fit for Vercel's serverless functions — host it on a persistent service.

**Render (easiest):**
1. New → Blueprint → point at this repo (`render.yaml` is included).
2. After the first deploy, set in the Render dashboard:
   - `ALLOWED_ORIGINS` = your Vercel URL(s), comma-separated, e.g.
     `https://dealopportunityos.vercel.app` (any `*.vercel.app` is already allowed
     by default).
   - `MAPBOX_TOKEN` (server-side geocoding) and `HUNTER_API_KEY` (email enrichment),
     if you use those features.
3. Copy the service URL and set it as `NEXT_PUBLIC_API_BASE` on Vercel (step 1.4).

**After the backend is live**, load data on it: open the deployed site's
`/review` page and import your Yardi / CoStar exports, and drop your HelloData
files where the market reference loads (or set `MARKET_REFERENCE_CSV`). The
SQLite DB and licensed data files are intentionally **not** in the repo.

## Notes

- CORS already allows `localhost` and any `*.vercel.app` origin; add a custom
  domain via `ALLOWED_ORIGINS`.
- Free Render instances sleep when idle and cold-start on the next request.
- Brand fonts under `frontend/src/fonts/` are licensed to InTrust — keep the repo
  private if that's a concern.
