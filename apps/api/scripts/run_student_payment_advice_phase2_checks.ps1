param(
    [switch]$SkipInstall
)

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_student_payment_advice_checks.ps1") @(
    if ($SkipInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Student payment advice Phase 2 API checks failed."
}

Write-Host "Student payment advice Phase 2 API checks passed."
