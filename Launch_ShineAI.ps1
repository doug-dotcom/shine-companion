$ErrorActionPreference = "Stop"
cd "C:\ShineAI"

# If venv exists, activate it
if (Test-Path ".\venv\Scripts\Activate.ps1") {
  . .\venv\Scripts\Activate.ps1
}

# Show env
Write-Host "AI_PROVIDER=$env:AI_PROVIDER"
if (-not $env:OPENAI_API_KEY) { Write-Host "OPENAI_API_KEY is NOT set" -ForegroundColor Yellow }

# Run
python .\server.py
