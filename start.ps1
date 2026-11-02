$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    Write-Host 'First run: creating an isolated Python environment.'
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ is required. Install Python and reopen this terminal.' }
    & '.venv/Scripts/python.exe' -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
Write-Host 'Open http://127.0.0.1:8001. Press Ctrl+C to stop.'
& '.venv/Scripts/python.exe' -m uvicorn server:app --host 127.0.0.1 --port 8001
