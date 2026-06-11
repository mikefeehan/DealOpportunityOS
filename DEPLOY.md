# Deploying OpportunityOS

This is a **monorepo**: a Next.js frontend in `frontend/` and a FastAPI backend in
`backend/`. They deploy to two different places.

## Why the Vercel 404 happens

Vercel builds from the repo **root** by default, but the Next.js app lives in
`frontend/`. With nothing at the root, Vercel serves nothing -> `404 NOT_FOUND`.

The repo now includes a root **`vercel.json`** that points the build at the
frontend, so this is handled for you.

## 1. Frontend on Vercel

1. Import this repo into Vercel.
2. **Leave Root Directory at the repo root (default / empty). Do NOT set it to
   `frontend`.** The `vercel.json` already builds `frontend/` via `@vercel/next`;
   setting Root Directory to `frontend` would double-nest and 404. (If you set it
   earlier, change it back to `./` and redeploy.)
3. **Environment Variables** (Settings -> Environment Variables):
   - `NEXT_PUBLIC_MAPBOX_TOKEN` - your Mapbox public token (maps).
   - `NEXT_PUBLIC_API_BASE` - the deployed backend URL (see part 2), e.g.
     `https://opportunityos-backend.onrender.com`. Without this the site loads but
     has no data.
4. Redeploy (Deployments -> the latest -> Redeploy).

## 2. Backend on Render (or Railway / Fly)

The backend is **stateful** (SQLite + uploaded files + on-demand imports), so it is
not a fit for Vercel's serverless functions - host it on a persistent service.

**Render (easiest):**
1. New -> Blueprint -> point at this repo (`render.yaml` is included).
2. After the first deploy, set in the Render dashboard:
   - `ALLOWED_ORIGINS` = your Vercel URL(s), comma-separated (any `*.vercel.app`
     is already allowed by default).
   - `MAPBOX_TOKEN` (server-side geocoding) and `HUNTER_API_KEY` (email
     enrichment), if you use those.
3. Copy the service URL and set it as `NEXT_PUBLIC_API_BASE` on Vercel (part 1.3).

**After the backend is live**, load data on it: open the deployed site's `/review`
page and import your Yardi / CoStar exports, and add your HelloData files where the
market reference loads. The SQLite DB and licensed data files are intentionally
**not** in the repo.

## Notes

- CORS already allows `localhost` and any `*.vercel.app` origin; add a custom
  domain via `ALLOWED_ORIGINS`.
- Free Render instances sleep when idle and cold-start on the next request.
- Brand fonts under `frontend/src/fonts/` are licensed to InTrust - keep the repo
  private if that's a concern.
