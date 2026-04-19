param(
    [switch]$SkipInstall
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiRoot = Resolve-Path (Join-Path $scriptDir "..")
$venvPath = Join-Path $apiRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"

if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment was not created successfully."
}

if (-not $SkipInstall) {
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r (Join-Path $apiRoot "requirements.txt")
}

Push-Location $apiRoot
try {
    & $pythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Pytest failed."
    }

    & $pythonExe scripts/phase_smoke.py
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke checks failed."
    }
}
finally {
    Pop-Location
}

Write-Host "All Phase 0/1 checks passed."

