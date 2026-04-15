# Project Agent Notes

This file is project-local guidance for `platforma_maga`. Global Codex policy remains the source of truth; use this file only for repository shape, local commands, and recurring project risks.

## First Read

1. Read `.codex/project-map/index.md`.
2. Read `.codex/project-map/00-overview.md`, `.codex/project-map/50-worklog.md`, and `.codex/project-map/30-changes.md`.
3. For coding work, inspect the touched modules directly. The project map is a startup aid, not a substitute for current source.

## Project Shape

- Backend: Python 3.11 FastAPI app in `backend/app`, SQLAlchemy/Alembic, Pydantic v2, Redis, Celery, Telegram/VK integrations, backup/export services.
- Frontend: Next.js 16, React 19, TypeScript, Vitest, Playwright smoke tests, Radix/lucide UI stack in `frontend/src`.
- Deploy: Docker Compose, nginx, VPS deploy/recovery scripts, GitHub Actions CI/CD in `deploy/` and `.github/workflows/`.
- Specs and historical context live in `.kiro/`, `md/`, `docs/`, and `.codex/project-map/`.

## Sensitive Files

- Treat `backend/.env`, `deploy/.env*`, backup material, logs, and any token/key-bearing files as read-only unless the user explicitly asks for a specific safe edit.
- Do not paste secrets or real credential values into docs, tests, commits, or final responses.

## Current Hot Areas

- Labs, schedule, journal, attestation, deadline, and submission flows are tightly coupled. Check both backend services and frontend read surfaces before changing behavior.
- Deadline behavior should stay centralized through the existing shared helpers and trace/read-model paths: `deadline_engine`, `deadline_inputs`, `deadline_context`, `deadline_trace`, visibility services, and matching tests.
- Submission state changes should use the shared transition layer instead of ad hoc status/field mutation.
- Avoid reintroducing divergent `subject_id + work_number`, stale `lesson_id`, subgroup, EXCUSED, extension, or legacy fallback semantics.
- Recent work also touched dashboard/report performance, admin lectures/labs navigation, deploy static checks, schedule attendance, auth fingerprint/session handling, public reports, backup/recovery, and rate limiting.

## Local Verification

Use the smallest meaningful subset for the files changed. Prefer the same gates CI uses.

Backend:

```bash
cd backend
ruff check app
ruff format --check app
python scripts/check_mypy_regressions.py
pytest -v --tb=short -m "not smoke and not integration and not exploratory"
pytest -v --tb=short -m smoke
```

Backend integration and migrations, when database behavior changes:

```bash
cd backend
alembic upgrade head
pytest -v --tb=short -m integration
pytest -v --tb=short app/tests/integration/test_db_models.py
```

Frontend:

```bash
cd frontend
npx tsc --noEmit
npm run lint
npm test
npm run build
npm run test:smoke
```

Deploy scripts:

```bash
shellcheck -x deploy/install.sh deploy/rebuild.sh deploy/recovery.sh deploy/lib/common.sh deploy/lib/envfile.sh deploy/lib/prod_deploy.sh deploy/tests/deploy_static_checks.sh
bash deploy/tests/deploy_static_checks.sh
```

## Local Run

- Frontend only: `cd frontend && npm run dev`.
- Docker dev stack: `./deploy/start-dev.sh`, with `--build`, `--no-build`, or `--clean-next` when needed.
- Do not stop, rebuild, or restart containers unless the user asked for runtime changes or the task cannot be verified otherwise.

## Project Notes

- Keep one live task file per active workstream under `.codex/project-map/tasks/`.
- After meaningful changes, refresh `.codex/project-map/` with the project-memory-map script and add short `done`, `pending`, or `handoff` notes when useful.
- Keep this `AGENTS.md` short and stable. Put volatile task details in project-map task files, not here.
