# Technical Debt Remediation Checklist

Date: 2026-03-28
Scope: backend, frontend, deploy, CI, tests, migration hygiene
Mode: research only, no code edits in this document

## Goal

Собрать один рабочий план устранения накопившегося техдолга без хаотичных "массовых рефакторингов".
План ориентирован на безопасную поэтапную стабилизацию перед дальнейшими релизами и переносом на VPS.

## Method

- Локальный baseline:
  - `.github/workflows/ci.yml`
  - `backend/pyproject.toml`
  - `frontend/package.json` и `frontend/package-lock.json`
  - локальный прогон CI-эквивалента
  - RMU quality-hotspots / rule-violations
  - локальная агрегация `mypy` и `eslint` долгов
- Агентская волна:
  - QA/test debt агент отработал полностью
  - backend/frontend/dependency/cross-cutting агентские сессии частично деградировали из-за проблем среды
  - по не вернувшимся зонам выводы добраны вручную локальной проверкой

## Baseline Facts

- Полный backend CI-эквивалент сейчас зелёный по `ruff` и `pytest`.
- `backend`:
  - `491 passed`
  - tracked `mypy` baseline artifact currently records `383 errors in 106 files`; regression gate is blocking, full raw `mypy app` is still not blocking
- `frontend`:
  - `tsc`, `build`, `npm audit` проходят
  - `eslint` зелёный по exit code, но остаётся `76 warnings`
- Security checks в CI не блокируют merge:
  - `mypy app || true`
  - `pip-audit ... || true`
  - `npm audit ... || true`
- Migration check проверяет только дубли номеров миграций, а не schema parity и не rollback safety.
- RMU quality summary:
  - `1233` нарушений
  - `780` violating files
  - статус quality-index: `stale`

## Agent Scorecard

| Agent      | Area                       |                Delivery | Score | Notes                                                                                             |
| ---------- | -------------------------- | ----------------------: | ----: | ------------------------------------------------------------------------------------------------- |
| `Socrates` | QA / test debt             |                complete | 4.7/5 | Полезный и конкретный отчёт, подтверждён локальным CI-анализом                                    |
| `Hume`     | deps / CI / security       |                 partial | 3.2/5 | Вместо bounded-отчёта создал черновой чеклист; полезно как артефакт, но не как чистый area report |
| `Laplace`  | backend debt               |       unstable delivery | 1.5/5 | Сессия стартовала, итог не вернулся; область закрыта вручную                                      |
| `Ptolemy`  | frontend debt              |       unstable delivery | 1.5/5 | Сессия стартовала, итог не вернулся; область закрыта вручную                                      |
| `Pascal`   | cross-cutting architecture |   failed in environment | 0.5/5 | Запуск развалился на уровне среды; синтез выполнен вручную                                        |
| `Newton`   | backend debt fast wave     | shutdown/no deliverable | 0.5/5 | Ускоренный перезапуск тоже не вернул итог                                                         |
| `Sagan`    | frontend debt fast wave    | shutdown/no deliverable | 0.5/5 | Ускоренный перезапуск тоже не вернул итог                                                         |

## Concrete Root-Cause Clusters

### Backend `mypy` debt by pattern

1. SQLAlchemy-typed model fields используются как обычные domain values.
   - Evidence:
     - `backend/app/services/rate_limit/models.py`
     - `backend/app/crud/crud_lesson_grade.py`
     - `backend/app/api/v1/endpoints/admin_reports.py`
2. Nullable/`Optional` handling не зафиксирован на boundary и протекает в сервисы.
   - Evidence:
     - `backend/app/services/storage.py`
     - `backend/app/tasks/schedule_tasks.py`
     - `backend/app/services/attestation/calculator.py`
3. Схемы и модели расходятся по enum/UUID contract.
   - Evidence:
     - `backend/app/services/reports/report_builder.py`
     - `backend/app/api/v1/endpoints/admin_reports.py`
     - `backend/app/api/v1/endpoints/admin_attendance.py`
4. Service-orchestrator functions знают слишком много и возвращают слишком широкие shape’ы.
   - Evidence:
     - `backend/app/services/journal_grade_service.py`
     - `backend/app/services/reports/data_collector.py`
     - `backend/app/services/student_lab_service.py`
5. Runtime/config/dependency injection плохо описаны для type-checking.
   - Evidence:
     - `backend/app/core/config.py`
     - `backend/app/db/session.py`
     - `backend/app/services/pdf_service.py`

### Frontend warning debt by pattern

1. `react-hooks/exhaustive-deps` в stateful admin/data hooks.
   - Evidence:
     - `frontend/src/components/admin/ActivityManagementSection.tsx`
     - `frontend/src/app/admin/journal/hooks/useJournalLessons.ts`
     - `frontend/src/components/labs/LabScheduleAttachment.tsx`
2. `@typescript-eslint/no-unused-vars` в editor/node/viewer cluster.
   - Evidence:
     - `frontend/src/components/lectures/nodes/*.ts*`
     - `frontend/src/components/lectures/LectureEditor.tsx`
3. React Hook Form `watch()` incompatible-library warnings в больших form-компонентах.
   - Evidence:
     - `frontend/src/components/admin/ComponentToggle.tsx`
     - `frontend/src/components/labs/editor/HeaderTab.tsx`
     - `frontend/src/components/notes/NoteButton.tsx`
4. Giant route components mix route/data/render/mutations.
   - Evidence:
     - `frontend/src/app/admin/groups/[id]/page.tsx`
     - `frontend/src/app/admin/journal/components/JournalTable.tsx`
     - `frontend/src/app/admin/audit/components/SecurityTab.tsx`
5. Shared fan-in hubs create hidden regression radius.
   - Evidence:
     - `frontend/src/lib/utils.ts`
     - `frontend/src/lib/api/types/attestation.ts`
     - `frontend/src/components/ui/sidebar.tsx`

## Main Debt Taxonomy

1. Non-blocking CI gates create false confidence.
2. Backend type debt is concentrated, structural, and clustered by root cause.
3. Several backend services are oversized orchestrators with mixed responsibilities.
4. Frontend has oversized admin/page components with route + data + rendering mixed together.
5. Frontend warning debt is not fatal, but it hides real refactor friction.
6. Test suite is large, but part of it is bug-memorial coverage rather than stable contract coverage.
7. Deploy/install surface is too monolithic and interactive for deterministic recovery work.
8. Some quality signals are stale or incomplete, so prioritization must rely on direct code evidence too.

## Highest-Risk Debt Items

### 1. CI policy debt

Evidence:

- `.github/workflows/ci.yml`
- `backend/pyproject.toml`

Problem:

- type checks and security audits are informational, not gating
- no dedicated frontend integration/smoke stage
- migration check is too shallow

Risk:

- green CI does not equal safe merge

Checklist:

- [x] Make `mypy` gating blocking via tracked regression baseline; full raw `mypy app` blocking still deferred until reduction wave
- [x] Add blocking smoke checks for critical backend flows
- [x] Add blocking frontend smoke/integration job
- [x] Extend migration checks beyond numbering only

Definition of done:

- [x] CI blocks merges on critical regressions, not just syntax/build failures

### 2. Backend type debt clusters

Evidence:

- top local `mypy` clusters:
  - `backend/app/services/rate_limit/admin.py` `21`
  - `backend/app/services/reports/data_collector.py` `15`
  - `backend/app/services/rate_limit/models.py` `14`
  - `backend/app/services/journal_grade_service.py` `13`
  - `backend/app/services/reports/attendance_helpers.py` `12`
  - `backend/app/services/announcement_service.py` `12`

Root causes:

- SQLAlchemy model attributes typed as domain values
- `Optional` / nullable handling debt
- schema-model enum mismatch
- service functions returning broader shapes than declared

Checklist:

- [x] Split `mypy` debt into root-cause classes, not file-by-file whack-a-mole
- [x] Fix SQLAlchemy typing patterns in rate-limit and journal/report clusters first
- [ ] Standardize UUID and enum boundary typing
- [x] Add a tracked mypy baseline artifact before making the gate blocking

Definition of done:

- top 20% noisiest files no longer dominate the error budget

Progress update 2026-03-30:

- completed first remediation wave for `rate-limit`, `reports`, `journal`-adjacent and `announcement` type-debt paths
- rate-limit legacy SQLAlchemy typing moved off old `Column[...]` annotations; timezone-aware UTC and focused contract tests added
- report cluster split by responsibility (`attendance_timeline_helpers`, `student_detail_collector`, `visibility_helpers`) and enum boundary unified at schema/model edge
- regression gate is green via `backend/scripts/check_mypy_regressions.py`; targeted backend verification passed
- DoD is not fully met yet: the tracked baseline still needs a deliberate shrink/update pass, and the top-20%-dominance metric has not yet been closed

### 3. Rate-limit admin path is structurally brittle

Evidence:

- `backend/app/services/rate_limit/admin.py`

Problem:

- query construction, DTO mapping, Redis cleanup, and admin actions live together
- code still uses `datetime.utcnow()`
- current shape directly correlates with highest `mypy` file count

Checklist:

- [x] Extract query builder / repository layer from admin orchestration
- [x] Extract Redis unban side effects into a dedicated helper
- [x] Normalize datetime handling to timezone-aware UTC
- [x] Add contract tests for active-ban filtering and unban side effects

Progress update 2026-03-30:

- admin path split into orchestration, query/repository, and Redis cleanup helpers
- focused service and endpoint contracts added for active bans, history filters, and unban flows
- targeted verification passed: `ruff`, scoped `mypy`, `pytest tests/test_rate_limit_admin.py tests/test_rate_limit_admin_endpoints.py`, and `backend/scripts/check_mypy_regressions.py`
- stale resolved `mypy` baseline entries for `app/services/rate_limit/admin.py` removed

Definition of done:

- [x] file no longer acts as query-builder + mutator + serializer at once

### 4. Report aggregation logic is split across many helpers but still inconsistent

Evidence:

- `backend/app/services/reports/data_collector.py`
- `backend/app/services/reports/attendance_helpers.py`
- `backend/app/services/attestation/attendance_calculator.py`

Problem:

- reports and attestation use diverging attendance formulas
- facade class still knows too much about low-level orchestration
- TODO in code explicitly admits formula drift

Checklist:

- [x] Define one canonical attendance/grade contract for report vs attestation
- [x] Separate data-fetch phase from derivation phase
- [x] Add invariant tests for formula parity decisions
- [x] Document intentional divergences if any remain

Progress update 2026-03-30:

- added shared `attendance_contract.py` and `attendance_period.py` as the canonical report/attestation/export attendance layer
- report and student-detail attendance now use the selected attestation period instead of mixing period-aware scores with wider attendance windows
- export attendance rows now delegate to the shared report attendance derivation path
- intentional divergence is versioned in `md/audits/attendance-contract-v1.md`: student period attendance vs attestation score vs lesson-level history metric
- invariant coverage added in `backend/tests/test_attendance_contract.py` and `backend/tests/test_attendance_contract_refactor.py`; `all EXCUSED => full credit` is now asserted explicitly

Definition of done:

- formula differences are either removed or explicitly versioned and tested

### 5. Backup/recovery cluster is oversized and operationally risky

Evidence:

- `backend/app/services/backup/backup_service.py`
- `backend/app/services/backup/restore_service.py`
- `backend/app/services/backup/notification.py`
- `backend/app/services/backup/remote_storage.py`
- `deploy/install.sh`

Problem:

- backup code mixes orchestration, encryption, upload, notification, cleanup
- restore/backup paths sit in a large cluster with cycle signals
- install script is `736` lines and interactive, which reduces reproducibility

Checklist:

- [x] Split backup flow into dump/compress/encrypt/upload/notify modules
- [x] Add explicit restore smoke path on disposable environment
- [x] Move interactive installer logic into smaller idempotent steps
- [x] Add non-interactive deploy/recovery mode with explicit inputs

Progress update 2026-03-30:

- backup cluster split into focused modules: `artifact_ops.py`, `compression.py`, `dump_runner.py`, `notification_sync.py`, `results.py`, `storage_utils.py`, `upload_flow.py`
- `backup_service.py` and `restore_service.py` reduced to thinner orchestrators; package-level re-export fan-out removed from `app.services.backup`
- added explicit restore rehearsal CLI in `backend/app/scripts/backup_rehearsal.py`
- added disposable recovery path in `deploy/recovery.sh`
- `deploy/install.sh` and `deploy/rebuild.sh` now delegate to idempotent shared helpers in `deploy/lib/*.sh`
- non-interactive deploy/recovery flow is explicit via `--env-file` / `--non-interactive`
- targeted verification passed: backup/restore pytest wave, shell syntax checks for deploy scripts, and install/recovery CLI help checks

Definition of done:

- [x] backup and restore can be rehearsed deterministically without manual branching

### 6. Frontend admin/page components are too large and too coupled

Evidence:

- `frontend/src/components/ui/sidebar.tsx` `775 lines`
- `frontend/src/app/admin/groups/[id]/page.tsx` `396 lines`
- `frontend/src/app/admin/journal/components/JournalTable.tsx` `321 lines`
- `frontend/src/app/admin/audit/components/SecurityTab.tsx` `380 lines`
- `frontend/src/components/admin/ActivityManagementSection.tsx` `351 lines`

Problem:

- route logic, derived state, rendering, and actions are mixed
- large components are harder to test and easier to regress

Checklist:

- [x] Split route containers from presentational subpanels
- [x] Extract pure view-model helpers from big render functions
- [x] Move data-fetching and mutation orchestration into hooks/services
- [x] Prioritize admin journal, audit, groups, and activity screens first

Progress update 2026-04-01:

- admin `groups/[id]`, `journal`, `audit/security`, and `activity` flows were split into thin containers, focused hooks, and presentational subcomponents
- shared pure helpers/view-model modules were extracted for student import parsing, journal table derivations, security tab mapping, and activity grouping; targeted Vitest coverage was added for the new pure modules
- follow-up refactors also reduced `schedule` and `settings/backup` admin flows below the local monolith threshold, so the remaining large `sidebar.tsx` UI primitive is no longer a blocker for this admin-specific item
- verification passed for targeted frontend tests, `npx tsc --noEmit`, and linting of the touched frontend surface; `npm run build` remained blocked by a local permission issue on `frontend/.next`, not by the refactor itself

Definition of done:

- [x] no critical admin screen depends on a single 300+ line stateful component

### 7. Frontend warning debt is concentrated by pattern

Evidence:

- 2026-04-01 remediation wave completed for frontend lint debt
- `frontend/src` eslint baseline is now `0 warnings`, `0 errors`
- `react-hooks/exhaustive-deps` suppressions removed from stateful admin/data hooks and the last two out-of-scope holdouts:
  - `frontend/src/app/report/[code]/PublicReportClient.tsx`
  - `frontend/src/app/admin/announcements/AnnouncementDialog.tsx`
- lecture/editor node and viewer cluster cleaned in one isolated sweep; `no-unused-vars` stopped dominating the warning budget
- React Hook Form `watch()` remains only in a few non-warning callsites; high-friction form paths already use field subscriptions where that warning debt previously mattered

Patterns:

- `react-hooks/exhaustive-deps` suppression debt in stateful hooks
- `@typescript-eslint/no-unused-vars` noise in lecture/editor cluster
- React Hook Form `watch()` friction was adjacent, but not part of the final active warning baseline

Checklist:

- [x] Separate cosmetic warnings from behavior-risk warnings
- [x] Fix hook dependency warnings in stateful admin/data hooks first
- [x] Replace repeated `watch()` inline calls with safer field subscriptions where needed
- [x] Clean generated/editor node noise in one isolated sweep

Definition of done:

- [x] warning budget dropped to zero and no `react-hooks/exhaustive-deps` suppressions remain in `frontend/src`

### 8. Oversized tests create false confidence

Evidence:

- former `backend/tests/test_attestation_audit_bugs.py` memorial suite
- former `backend/tests/journal_submission_sync/test_sync_from_journal.py` memorial suite
- auth/session/device cluster
- QA agent findings

Problem:

- large bug-preservation suites overfit implementation details
- missing explicit smoke/integration layers for critical flows

Checklist:

- [x] Freeze critical smoke flows before major refactors
- [x] Convert bug-memorial suites into smaller contract/invariant groups
- [x] Add integration tests for auth/session, journal sync, backup/restore, audit filters
- [x] Add property-style tests where invariants matter more than examples

Definition of done:

- test suite gives trustworthy signal on user-visible flows and invariants

Progress update 2026-04-02:

- split oversized attestation/device/journal memorial suites into smaller preservation and contract files
- added smoke coverage for canonical journal projection, backup/restore routes, and admin audit filter flows
- added integration coverage for Redis-backed session lifecycle, DB-backed journal projection, DB-backed audit filters, and backup/restore service boundary
- added property-style invariant checks for session privacy masking

### 9. Deploy/install path is a monolith

Evidence:

- `deploy/install.sh`

Problem:

- one script mixes detection, prompting, Docker install, swap, env loading, deployment
- high blast radius on edits

Checklist:

- [ ] Split into validate / prepare-host / configure-env / deploy / verify subcommands
- [x] Make non-interactive mode first-class
- [x] Add shell tests or dry-run mode for critical branches

Progress update 2026-03-30:

- install/rebuild flow split across `deploy/lib/common.sh`, `deploy/lib/envfile.sh`, and `deploy/lib/prod_deploy.sh`
- interactive install UX preserved in a smaller `install.sh`, while non-interactive operation is now a first-class path
- dedicated `recovery.sh` added for deterministic disposable restore rehearsal
- follow-up static coverage added in `deploy/tests/deploy_static_checks.sh` and wired into CI via a dedicated `deploy-static` job with `shellcheck`
- operator docs in `deploy/VPS_SETUP.md` now point to the canonical `install.sh` / `rebuild.sh` / `recovery.sh` flow instead of manual compose-first steps
- true subcommand split remains open

Definition of done:

- [x] operator can run deterministic install/recovery with replayable inputs

### 10. Quality instrumentation itself needs maintenance

Evidence:

- RMU quality status: `stale`

Problem:

- hotspot rankings are useful, but not fresh enough to be the only prioritization source

Checklist:

- [ ] Refresh quality index after each debt wave
- [ ] Store before/after snapshots per wave
- [ ] Track line-count and warning-count deltas as explicit KPIs

Definition of done:

- prioritization is driven by current data, not stale one-off scans

## Remediation Program

### Wave 0. Safety Rails

- [ ] Freeze current CI baseline and current warning/error counts
- [x] Add lightweight smoke tests for:
  - auth/session/impersonation
  - journal sync
  - backup/restore happy path
  - audit exclusion behavior
- [ ] Refresh RMU quality index

Exit criteria:

- critical flows have executable smoke coverage before refactors start

### Wave 1. CI Truthfulness

- [x] Add frontend smoke/integration job
- [x] Add backend integration job for critical flows
- [x] Tighten migration consistency checks
- [x] Publish tracked baseline artifact and switch type/security policy from informational checks to blocking regression gates

Exit criteria:

- [x] CI failures correlate with real regression risk

### Wave 2. Backend Debt Burn-Down

- [x] Refactor `rate_limit` typing/orchestration cluster
- [x] Refactor report aggregation formula and helper split
- [x] Start backup/restore service decomposition
- [x] Reduce top mypy clusters by root cause

Exit criteria:

- [x] top backend hotspots stop dominating both type debt and future change risk

Evidence:

- `backend/app` passes `mypy` cleanly (`0` errors)
- mypy regression gate reports `0 tracked errors, 0 regressions`
- `mypy-baseline.txt` was refreshed to a zero-error baseline
- warning-gated backend smoke/contract slice passes with `123 passed` under `-W error::DeprecationWarning`

### Wave 3. Frontend Debt Burn-Down

- [x] Split giant admin pages and admin sidebar composition
- [x] Reduce hook-warning debt in stateful flows
- [x] Isolate editor/node warning cleanup
- [x] Break route/data/render coupling in journal/audit/groups/admin settings

Exit criteria:

- critical frontend screens are smaller, testable, and less cycle-prone

Evidence:

- `AdminSidebar` was split into nav/config/count-hook layers; shared `frontend/src/components/ui/sidebar.tsx` remains a separate follow-up debt track
- `admin/groups/[id]` now uses smaller route shell + data hook + UI-state hook + extracted header/tab components
- `admin/settings` now uses a thin page shell with extracted profile/session/backup helpers
- smoke coverage now exercises `journal`, `audit`, `groups`, and `settings` high-risk admin flows

### Wave 4. Test Suite Recomposition

- [x] Break up oversized bug-preservation suites
- [x] Promote invariant-heavy logic to property tests
- [x] Keep a smaller but stronger regression suite
- [x] Remove redundant low-signal tests only after replacement coverage exists

Exit criteria:

- faster, more trustworthy test signal

Evidence:

- added property tests for `studentImport` and `journalTableModel`
- `useFeedbackForm` preservation/bug suites were slimmed around shared helpers instead of keeping duplicated narrative setup
- replacement coverage landed before shrinking low-signal assertions
- frontend unit suite stays green at `25` files / `67` tests

### Wave 5. Ops and Recovery Hardening

- [ ] Split `deploy/install.sh`
- [ ] Rehearse backup/restore on disposable environment
- [ ] Add deterministic recovery notes and verification checklist
- [ ] Re-check readiness for VPS migration after code and CI cleanup

Exit criteria:

- deploy/recovery is deterministic and operator-friendly

## Verification Gates Per Wave

### Wave 0 gates

- [ ] Current counts captured:
  - `mypy` total errors and top 20 files
  - ESLint warnings by file and by rule family
  - RMU hotspots snapshot
- [x] Smoke tests added without broad refactor
- [ ] Baseline doc committed separately from implementation work

### Wave 1 gates

- [x] CI has at least one frontend smoke/integration job
- [x] CI has at least one backend integration/smoke job
- [x] Security and migration jobs emit actionable failure output
- [x] New gates do not rely on `|| true` for critical checks

### Wave 2 gates

- [ ] Top backend hotspot files are split or responsibility-reduced
- [ ] `mypy` error count drops materially in top root-cause clusters
- [ ] No backend contract regressions in smoke/integration suites
- [ ] Report vs attestation invariants explicitly tested

### Wave 3 gates

- [x] Critical admin pages/components are below monolith threshold or split by responsibility
- [x] Hook-warning count drops in high-risk files first
- [x] UI smoke tests cover journal/audit/groups/settings high-risk flows
- [x] Shared hubs keep stable contract tests after refactor

### Wave 4 gates

- [x] Oversized test suites are decomposed only after replacement coverage exists
- [x] Invariant-heavy logic moved to property/contract testing where appropriate
- [x] Test runtime and failure readability improve, not just test count

### Wave 5 gates

- [ ] Backup/restore rehearsal documented and repeatable
- [ ] `deploy/install.sh` responsibilities split or wrapped in deterministic subcommands
- [ ] VPS migration readiness reviewed against updated CI and recovery evidence

## Priority Order

1. CI truthfulness
2. Backend high-leverage clusters
3. Frontend giant components and warning-risk clusters
4. Test suite recomposition
5. Deploy/install decomposition

## What Not To Do

- Do not make `mypy` blocking before shrinking the dominant error clusters.
- Do not run a giant repo-wide formatting/refactor wave mixed with debt cleanup.
- Do not split big tests before smoke coverage exists for the same user flow.
- Do not touch deploy/install and backup/restore in the same unverified release.

## Next Actionable Starting Set

- [ ] Create a tracked debt baseline doc with current counts
- [x] Add one backend smoke suite for auth/session/audit
- [ ] Add one frontend smoke suite for admin journal and audit
- [ ] Refactor `backend/app/services/rate_limit/admin.py`
- [ ] Refactor `backend/app/services/reports/data_collector.py`
- [ ] Split `frontend/src/app/admin/journal/components/JournalTable.tsx`
- [ ] Split `frontend/src/components/ui/sidebar.tsx`
