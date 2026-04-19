param(
    [switch]$SkipInstall
)

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_phase3_checks.ps1") @(
    if ($SkipInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Phase 4 API checks failed."
}

Write-Host "Phase 4 API checks passed."
