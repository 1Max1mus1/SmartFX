param(
    [switch]$SkipApiInstall,
    [switch]$SkipWebInstall
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps/api"
$webRoot = Join-Path $repoRoot "apps/web"

Write-Host "==> Running API Phase 2 checks"
powershell -ExecutionPolicy Bypass -File (Join-Path $apiRoot "scripts/run_phase2_checks.ps1") @(
    if ($SkipApiInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "API Phase 2 checks failed."
}

Write-Host "==> Running web build checks"
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

Write-Host "All Phase 2 repository checks passed."

