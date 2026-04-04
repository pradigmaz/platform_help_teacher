# Technical Debt Baseline

Date: 2026-04-04
Scope: backend, frontend, CI parity, dependency audit, RMU quality snapshot
Mode: verified from the current local workspace

## Summary

- `backend` local gates:
  - `ruff check app` passes
  - `python scripts/check_mypy_regressions.py` passes with `0 tracked errors, 0 regressions`
  - raw `mypy app` is clean
  - smoke suite passes: `50 passed, 561 deselected`
  - integration suite is not locally self-contained; without CI service containers it times out on the first PostgreSQL-backed test
- `frontend` local gates:
  - `npm ci` completed after rebuilding the local `node_modules` directory with the current user as owner
  - `npm run lint` passes
  - `npx tsc --noEmit` passes
  - `npm test` passes: `25` files / `67` tests
  - `npm audit --audit-level=high` reports `0 vulnerabilities`
  - production build passes in the repo after rotating the legacy foreign-owned `frontend/.next` tree into an ignored backup path
  - browser smoke passes from the repo: `7 passed`
- local repo build parity is restored:
  - direct `frontend/npm run build` now succeeds in the working tree
  - browser smoke still requires an escalated localhost listener because Playwright starts a local web server
  - legacy `frontend/.next.backup.*` trees remain ignored local artifacts because their old ownership blocks in-place cleanup
- dependency audit:
  - `backend/venv/bin/pip-audit -r requirements.txt`: `No known vulnerabilities found`
- RMU quality snapshot is fresh:
  - status: `ready`
  - `573` active violations across `432` files

## Verified Commands

### Backend

- `venv/bin/python -m ruff check app`
- `venv/bin/python scripts/check_mypy_regressions.py`
- `venv/bin/python -m mypy app --hide-error-context --no-color-output --no-error-summary`
- `venv/bin/python -m pytest -q -m smoke`
- `timeout 90s venv/bin/python -m pytest -m integration -x -vv`
- `timeout 60s venv/bin/pip-audit -r requirements.txt`

Observed results:

- `ruff`: green
- mypy regression gate: green
- raw mypy: green
- smoke: `50 passed, 561 deselected in 5.72s`
- integration: first DB-backed test times out locally because the suite expects real PostgreSQL/Redis services
- `pip-audit`: no known vulnerabilities

### Frontend

- `npm ci`
- `npm run lint`
- `npx tsc --noEmit`
- `npm test`
- `npm audit --audit-level=high`
- `npm run build`
- `npm run test:smoke`

Observed results:

- lint: green
- typecheck: green
- unit tests: `25` files / `67` tests green
- `npm audit`: `found 0 vulnerabilities`
- build: green in the repo
- smoke: `7 passed`

## CI Parity Notes

- `frontend-browser-smoke` already builds the frontend and runs browser smoke in CI.
- `backend-integration` provisions PostgreSQL and Redis before running integration tests.
- `backend-types` only enforces regression drift via `scripts/check_mypy_regressions.py`; raw full `mypy app` is locally clean but still not a dedicated CI gate.
- `security-audit` is now blocking for both `pip-audit` and `npm audit`; the older `|| true` posture no longer matches the workflow.

## Roadmap Delta

Closed/stale items from the 2026-03-28 checklist:

- frontend smoke for admin journal/audit is already covered
- `backend/app/services/rate_limit/admin.py` is already below the monolith threshold
- `backend/app/services/reports/data_collector.py` has been split into a thin facade plus focused collectors
- `frontend/src/app/admin/journal/components/JournalTable.tsx` is already below the monolith threshold
- `frontend/src/components/ui/sidebar.tsx` has been split into focused sidebar modules

Still-open high-signal items:

- `deploy/install.sh` still has an open subcommand split follow-up
- legacy ignored `frontend/.next.backup.*` trees still need out-of-band cleanup if ownership normalization on disk matters

## RMU Snapshot

- status: `ready`
- total violations: `573`
- violating files: `432`
- top hotspot buckets:
  - `backend/alembic/versions`
  - `backend/tests`
  - `backend/app/crud`
  - `backend/app/services`
  - `backend/app/api/v1/endpoints`
