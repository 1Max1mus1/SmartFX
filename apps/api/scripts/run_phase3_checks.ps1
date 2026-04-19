param(
    [switch]$SkipInstall
)

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_phase2_checks.ps1") @(
    if ($SkipInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Phase 3 API checks failed."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiRoot = Resolve-Path (Join-Path $scriptDir "..")
$pythonExe = Join-Path (Join-Path $apiRoot ".venv") "Scripts\\python.exe"

Push-Location $apiRoot
try {
    & $pythonExe scripts/run_daily_report_job.py
    if ($LASTEXITCODE -ne 0) {
        throw "Daily report job entry point failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Phase 3 API checks passed."
