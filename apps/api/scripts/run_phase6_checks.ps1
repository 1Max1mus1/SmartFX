param(
    [switch]$SkipInstall
)

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_phase5_checks.ps1") @(
    if ($SkipInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Phase 6 API checks failed."
}

Write-Host "Phase 6 API checks passed."
