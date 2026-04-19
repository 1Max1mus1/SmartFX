# SmartFX Launch Checklist

## Environment

- Copy `apps/api/.env.example` into a real runtime env file and replace all secrets.
- Copy `apps/web/.env.example` into `.env.local` or platform-managed env vars.
- Confirm `APP_ENV`, `APP_SECRET_KEY`, database URL, and provider API keys are set correctly.

## Release Gates

- Run `powershell -ExecutionPolicy Bypass -File .\scripts\run_phase7_checks.ps1`
- Confirm API health endpoints return `200`:
  - `/api/health`
  - `/api/health/live`
  - `/api/health/ready`
- Confirm the GitHub Actions workflow passes on the target branch.

## Runtime Checks

- Verify the desktop web app can load `/`, `/report`, `/assistant`, `/records`, and all `/pro/*` pages.
- Verify request tracing headers are present: `x-request-id`, `x-process-time-ms`.
- Verify the daily report job entry can run without errors.
- Verify backtest and pro report polling flows complete successfully.

## Compliance Checks

- Confirm every AI output path still includes the disclaimer.
- Confirm semi-auto rules only send notifications and never execute a real exchange.
- Confirm visible copy stays in the “reference / signal / reminder” boundary.

## Rollback Readiness

- Keep the previous web build and API deployment artifact available.
- Keep the previous environment variable set archived.
- If runtime checks fail after deploy, roll back web and API together to the last green Phase 7 build.
