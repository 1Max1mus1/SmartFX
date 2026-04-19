param(
    [switch]$SkipInstall
)

$apiRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPath = Join-Path $apiRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"

powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_phase6_checks.ps1") @(
    if ($SkipInstall) { "-SkipInstall" }
)

if ($LASTEXITCODE -ne 0) {
    throw "Phase 7 API checks failed."
}

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment was not created successfully."
}

Push-Location $apiRoot
try {
    & $pythonExe -m compileall src
    if ($LASTEXITCODE -ne 0) {
        throw "API compile check failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Phase 7 API checks passed."
