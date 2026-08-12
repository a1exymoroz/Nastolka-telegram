# Run the bot locally against .env.local (long polling, no public URL needed).
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path .env.local)) {
    Write-Error ".env.local not found - copy .env.example to .env.local and fill it in first."
    exit 1
}

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

& .venv\Scripts\pip.exe install -q -r requirements.txt
& .venv\Scripts\python.exe -m bot.main
