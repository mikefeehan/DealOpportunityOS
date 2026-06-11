$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\python -m pip install -r requirements.txt

Push-Location frontend
npm install
Pop-Location

Start-Process -WindowStyle Hidden -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"
Start-Process -WindowStyle Hidden -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory ".\frontend"

Write-Host "OpportunityOS is starting:"
Write-Host "Backend:  http://127.0.0.1:8000/api/health"
Write-Host "Frontend: http://localhost:3000"
