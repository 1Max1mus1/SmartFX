param(
    [switch]$SkipInstall
)

$apiRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPath = Join-Path $apiRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment was not found at $pythonExe"
}

Push-Location $apiRoot
try {
    if (-not $SkipInstall) {
        & $pythonExe -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "pip install failed."
        }
    }

    & $pythonExe -m pytest tests/test_student_payment_advice.py
    if ($LASTEXITCODE -ne 0) {
        throw "student payment advice pytest suite failed."
    }

    & $pythonExe scripts/student_payment_advice_smoke.py
    if ($LASTEXITCODE -ne 0) {
        throw "student payment advice smoke checks failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Student payment advice Phase 1 checks passed."
