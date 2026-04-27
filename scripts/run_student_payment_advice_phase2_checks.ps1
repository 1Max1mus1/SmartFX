param(
    [switch]$SkipApiInstall
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps/api"

Write-Host "==> Running student payment advice Phase 2 API checks"
powershell -ExecutionPolicy Bypass -File (Join-Path $apiRoot "scripts/run_student_payment_advice_phase2_checks.ps1") @(
    if ($SkipApiInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Student payment advice Phase 2 repository checks failed."
}

Write-Host "Student payment advice Phase 2 repository checks passed."
