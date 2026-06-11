# OpportunityOS - Tucson Pilot

Internal acquisition intelligence platform for InTrust Property Group.

The app answers one operational question:

> Who are the 25 apartment owners in Tucson we should call this week?

## Stack

- Backend: FastAPI, SQLite, SQLAlchemy
- Frontend: Next.js, TypeScript, Tailwind, shadcn-style UI components
- AI: OpenAI Responses API for narrative call prep only

## Run Locally

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Notes

- The backend attempts configured authorized inventory sources plus Tucson/Pima public parcel sources when the Tucson Scan button runs.
- If any live source fails or lacks enough 50+ unit multifamily data, seeded Tucson pilot data is loaded automatically.
- Scoring and ranking are deterministic. OpenAI is used only for Why Now, outreach, summaries, and call prep copy.
- The homepage is Top Owners To Call and is sorted by Call Score.
- Do not put Yardi, RealPage, or HelloData credentials in Git. Use local environment variables or session cookies only.
