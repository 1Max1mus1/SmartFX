param(
    [switch]$SkipApiInstall,
    [switch]$SkipWebInstall
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$webRoot = Join-Path $repoRoot "apps/web"

Write-Host "==> Running student payment advice Phase 2 API checks"
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_student_payment_advice_phase2_checks.ps1") @(
    if ($SkipApiInstall) { "-SkipApiInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Student payment advice Phase 2 API checks failed."
}

Write-Host "==> Running student payment advice Phase 3 web build"
Push-Location $webRoot
try {
    if (-not $SkipWebInstall) {
        npm install
        if ($LASTEXITCODE -ne 0) {
            throw "npm install failed."
        }
    }

    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "npm run build failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Student payment advice Phase 3 repository checks passed."
