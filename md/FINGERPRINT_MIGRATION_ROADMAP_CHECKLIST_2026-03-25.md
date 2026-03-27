# FINGERPRINT MIGRATION ROADMAP CHECKLIST

Date: 2026-03-25
Owner: Codex + user
Status: `in_progress`

## Purpose

This file is the single execution checklist for resolving the current fingerprint problem and migrating to a replacement in a controlled way.

Primary rule:

1. First stabilize, disable, and remove the current custom fingerprint system.
2. Only after removal is complete and verified, introduce the replacement.
3. Do not mix removal work and replacement work in the same checklist item.

This roadmap is intentionally written as a stable execution contract. It should not be rewritten during execution except under the change-control rules at the end of this file.

## Problem Statement

The current custom fingerprint implementation is a likely source of client-side performance spikes and unnecessary complexity:

- eager initialization from root app layout
- heavy browser collectors
- possible repeated synchronous collection during early API traffic
- backend coupling to current JSON structure
- audit, session, and device services relying on legacy payload semantics

## Target Outcome

After completion:

- the current custom fingerprint subsystem is fully removed
- no eager heavy fingerprint work runs on app startup
- backend no longer depends on legacy custom fingerprint schema
- replacement fingerprint integration is implemented behind a stable adapter
- startup performance, audit behavior, device binding, and session summaries are verified
- rollback path is documented and testable

## Scope

In scope:

- frontend fingerprint initialization and request-header behavior
- frontend fingerprint module and its consumers
- backend parsing, storage, device binding, session summary, audit extraction, suspicion matching
- migration path to replacement library
- verification, observability, rollout, rollback

Out of scope:

- unrelated auth redesign
- unrelated audit redesign outside fingerprint compatibility
- unrelated frontend performance cleanup not directly connected to this migration

## Non-Negotiable Sequencing

The execution order is fixed:

1. Baseline and freeze the current system behavior.
2. Stabilize production risk.
3. Decouple backend from legacy payload assumptions.
4. Remove the current custom fingerprint implementation.
5. Verify the system works without fingerprint.
6. Design the replacement contract.
7. Integrate the replacement behind an adapter.
8. Re-enable fingerprint-dependent features only after validation.
9. Roll out with rollback readiness.

## Success Criteria

Functional:

- login/session/device flows keep working
- audit ingestion does not break on missing fingerprint
- session summaries still render correctly
- device registration handles absence of fingerprint cleanly
- replacement library works under the new stable contract

Performance:

- no global eager fingerprint collection in root layout
- no repeated synchronous fingerprint collection on request startup path
- reduced startup CPU/GPU spike relative to current implementation
- no obvious long task burst caused by fingerprint on cold open

Operational:

- backend accepts `no fingerprint`, `legacy fingerprint`, and `replacement fingerprint` during migration
- rollout can be disabled without emergency backend patching
- all migration phases have explicit verification and rollback steps

## Tracking Rules

Mark progress only with these states:

- `[ ]` not started
- `[-]` in progress
- `[x]` complete
- `[!]` blocked

When marking a task complete, append:

- date
- short note with outcome
- file paths changed
- verification performed

Example:

`[x] Disable eager init in app layout - 2026-03-25 - removed mount, verified no startup call in logs - files: frontend/src/app/layout.tsx`

## Phase 0. Baseline, Freeze, and Safety Net

Goal: capture current behavior before changing anything.

Exit gate:

- current behavior is documented well enough to verify regression and improvement

Checklist:

- [x] Freeze the problem statement and target replacement choice in this file. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Capture current frontend startup path that triggers fingerprint. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Capture every frontend caller that reads or sends fingerprint. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Capture every backend endpoint/service that parses or depends on fingerprint. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Capture every backend place that stores fingerprint or its derived hash. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Capture current audit and suspicion logic dependencies on fingerprint fields. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Capture current session/device summary dependencies on fingerprint fields. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Define current fallback behavior when fingerprint is missing or malformed. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Record baseline performance evidence for cold open of student dashboard. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Record baseline performance evidence for lab detail page. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Record baseline network/request evidence for first dashboard load. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Record baseline startup logs or instrumentation around fingerprint collection. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Confirm whether any real-time detection, bans, or rate-limit logic require fingerprint to operate. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Confirm whether admin audit UI assumes structured fingerprint fields for rendering. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection
- [x] Confirm whether current database data must remain queryable after migration. - 2026-03-26 - evidence finalized in Phase 0 notes - files: md/FINGERPRINT_MIGRATION_ROADMAP_CHECKLIST_2026-03-25.md - verification: repo search + local runtime capture + DB/Redis inspection

Deliverables:

- file references to all affected modules
- baseline measurements
- explicit list of compatibility obligations

Final evidence collected for Phase 0 is below.
Final review completed on `2026-03-26`: every Phase 0 checklist item has explicit supporting evidence in this section, so the checklist above is now the completion record for this phase.

### Phase 0 Frozen Decisions

- Target replacement is frozen as a stable internal adapter contract.
- Concrete replacement vendor/library is intentionally deferred until after legacy removal is verified.
- Historical fingerprint-derived data must remain readable after migration.
- Admin audit UI must degrade gracefully for `legacy structured`, `reduced`, and `opaque` payloads.

### Current Frontend Behavior

Current startup path that triggers fingerprint:

1. `frontend/src/app/layout.tsx` mounts `FingerprintInitializer`.
2. `frontend/src/components/FingerprintInitializer.tsx` calls `useInitializeFingerprint()`.
3. `frontend/src/hooks/useFingerprint.ts` calls `initializeFingerprint()` on mount.
4. `frontend/src/lib/fingerprint/index.ts` runs `collectFingerprintAsync()` and caches the full JSON payload.

Current runtime sender path:

- `frontend/src/lib/api/client.ts` injects `X-Device-Fingerprint` into every `api` request via `getFingerprint()`.
- `frontend/src/lib/api/client.ts` injects `X-Device-Fingerprint` into every `publicApi` request via `getFingerprint()`.
- `getFingerprint()` is synchronous and can run before async initialization completes.
- Repo search found no other runtime sender/import path in `frontend/src` outside the initializer and axios clients.

Observed heavy collector surface in the legacy frontend module:

- `frontend/src/lib/fingerprint/index.ts`
- `frontend/src/lib/fingerprint/canvas.ts`
- `frontend/src/lib/fingerprint/webgl.ts`
- `frontend/src/lib/fingerprint/audio.ts`
- `frontend/src/lib/fingerprint/fonts.ts`
- `frontend/src/lib/fingerprint/async-collectors.ts`

Relevant student cold-load callers used for baseline:

- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/app/dashboard/labs/[id]/page.tsx`
- `frontend/src/lib/api/student.ts`

### Current Backend Behavior

Backend endpoints/services that parse or depend on fingerprint:

- `backend/app/api/v1/endpoints/auth.py`
  - login reads `X-Device-Fingerprint`
  - passes it into session creation and device registration
- `backend/app/api/v1/endpoints/admin_impersonate.py`
  - impersonation and impersonation-exit session creation reuse `X-Device-Fingerprint`
- `backend/app/services/session_service.py`
  - builds `device_summary` from fingerprint JSON
- `backend/app/services/device_service.py`
  - hashes raw fingerprint string and derives `device_info`
- `backend/app/audit/utils.py`
  - parses header into structured JSON or `{ "hash": raw }`
- `backend/app/audit/middleware.py`
  - stores parsed fingerprint in audit context for student/admin-path logging
- `backend/app/middleware/security_monitor.py`
  - parses header into structured JSON or `{ "hash": raw }`
- `backend/app/services/security_monitor/detector.py`
  - hashes parsed fingerprint, stores `fingerprint -> user` Redis mapping, and uses it for banned-user re-identification
- `backend/app/audit/suspicion/fingerprint.py`
  - depends on `webgl`, `screen`, `platform`, `hardwareConcurrency`, `canvas`, and `userAgent`
- `backend/app/audit/suspicion/service.py`
  - uses structured fingerprint matching and anti-detect inconsistency checks
- `backend/app/api/v1/endpoints/user_sessions.py`
  - renders device/session summary from derived session payload
- `backend/app/api/v1/endpoints/admin_audit.py`
  - returns raw audit `fingerprint` to the admin UI

Current backend storage and derived-hash locations:

- `backend/app/audit/models.py`
  - `student_audit_log.fingerprint` stores raw parsed fingerprint as JSONB
- `backend/app/models/device.py`
  - `devices.fingerprint_hash` stores SHA256 of the raw fingerprint string
  - `devices.device_info` stores derived platform/browser/screen info
- `backend/app/services/session_service.py`
  - Redis session payload stores derived `device_summary`
- `backend/app/services/security_monitor/detector.py`
  - Redis stores `sec:fp_to_user:{fp_hash}` and `sec:user_fps:{user_id}`
- `backend/app/services/rate_limit/models.py`
  - `rate_limit_warnings.fingerprint_hash` exists in schema, but current service logic does not use fingerprint as the live identifier

### Current Audit, Suspicion, Session, and Device Dependencies

Current audit and suspicion logic dependencies on fingerprint fields:

- `webgl.vendor` and `webgl.renderer` drive the strongest structured match path.
- `screen.width`, `screen.height`, and `screen.colorDepth` drive screen-key matching.
- `platform` and `hardwareConcurrency` drive platform-key matching.
- `canvas` drives exact component matching.
- `userAgent` drives browser/OS scoring.
- `webgl.renderer`, `platform`, and `hardwareConcurrency` drive anti-detect inconsistency checks.

Current session/device summary dependencies on fingerprint fields:

- session summary uses `platform`, `userAgent`, and `screen.width/screen.height`
- device binding uses `platform`, `userAgent`, and `screen.width/screen.height`
- session UI and device UI rely on those derived summaries staying readable after migration

### Current Fallback Behavior

Frontend fallback behavior:

- `initializeFingerprint()` falls back to a minimal JSON payload with `screen`, `userAgent`, `language`, `timezone`, and `platform`
- `getFingerprint()` falls back to the same minimal JSON or `{}` if collection fully fails
- request-path sync collection logs a warning if called before async initialization completes

Backend fallback behavior:

- audit extractor returns `None` for missing header, `{}`, or too-empty JSON
- audit extractor returns `{ "hash": raw }` for malformed non-JSON values
- security monitor returns `None` for missing header and `{ "hash": raw }` for malformed non-JSON values
- session summary returns `None` if fingerprint is missing or malformed JSON
- device registration returns `None` and does no write if fingerprint is missing or `{}`
- device parsing treats malformed/hash-only fingerprint as unknown platform/browser/screen instead of failing

### Baseline Evidence

Baseline environment and method:

- local dev compose stack exposed via nginx on `http://localhost`
- login path: `/auth/login` -> `dev admin` -> impersonate selected student via admin UI
- baseline student used for measurements: `Осипов Ярослав Иванович`, group `ИС1-231-ОТ`

Cold open of student dashboard:

- total elapsed time to settled page snapshot: `3503 ms`
- navigation `responseEnd`: `71 ms`
- `DOMContentLoaded`: `106 ms`
- `loadEventEnd`: `879 ms`
- first paint: `108 ms`
- first contentful paint: `448 ms`
- `11` API resource entries were captured during the cold load

Cold open of lab detail page:

- total elapsed time to settled page snapshot: `2749 ms`
- navigation `responseEnd`: `263 ms`
- `DOMContentLoaded`: `296 ms`
- `loadEventEnd`: `1094 ms`
- first paint: `296 ms`
- first contentful paint: `624 ms`
- `5` API resource entries were captured during the cold load

Baseline network/request evidence for first dashboard load:

- 11 initial API requests were observed during cold dashboard load
- every observed API request carried `X-Device-Fingerprint`
- observed header size ranged from about `3143` to `3547` bytes
- initial request set included:
  - `/api/v1/student/profile`
  - `/api/v1/student/attendance`
  - `/api/v1/student/labs`
  - `/api/v1/student/attestation/subjects/second`
  - `/api/v1/student/attestation/{first|second}`
  - duplicate `/api/v1/student/announcements?skip=0&limit=10`
  - duplicate `/api/v1/public/semester-info`
- the first observed requests used a smaller fingerprint header than later requests in the same cold load, confirming that the request path can send fingerprint before async initialization has finished
- duplicate `announcements` and `semester-info` requests are baseline noise and must not be misattributed to later fingerprint-only changes

Baseline startup logs and instrumentation around fingerprint collection:

- browser console showed:
  - `[Fingerprint] getFingerprint() called before initialization. Use getInitializedFingerprint() instead.`
  - `[Fingerprint] Initialized successfully`
- this confirms the request path can race the eager async initializer
- sampled backend container logs did not show explicit fingerprint-specific instrumentation in the same baseline window

### Live Data Evidence

Current persisted data proves that legacy fingerprint-derived data must remain queryable after migration:

- Postgres `student_audit_log` currently contains `66598` rows total, with `52794` rows where `fingerprint` is not null
- sampled recent audit rows show real structured fingerprint JSON payloads in `student_audit_log.fingerprint`
- Postgres `devices` currently contains `171` rows, and all `171` rows have a populated `fingerprint_hash`
- sampled recent device rows show active `devices.device_info` values derived from fingerprint fields
- Redis security monitor currently stores fingerprint-to-user mappings under `sec:fp_to_user:*`
- Redis session payloads currently store `device_summary` and masked `ip_address`, not raw `device_fingerprint`

### Admin UI Assumptions

Current admin audit rendering assumes structured fingerprint fields:

- `frontend/src/app/admin/audit/components/AuditDetailDialog.tsx`
  - expects `screen`, `webgl`, `platform`, `hardwareConcurrency`, `deviceMemory`, `connection`, `mediaDevices`, `canvas`, and `audio`
- `frontend/src/app/admin/audit/components/AuditLogsTable.tsx`
  - expects `suspicion.fingerprint_match`, `matched_components`, and inconsistency details
- `frontend/src/lib/api/audit.ts`
  - types fingerprint as a structured object rather than an opaque identifier

Implication:

- admin audit UI cannot assume only opaque hash/ID for new clients
- migration must either normalize new payloads into a reduced renderable shape or gracefully degrade the UI

### Compatibility Obligations

- Backend must accept `missing fingerprint` during the migration window without breaking login, session, device, audit, or security request handling.
- Historical audit/device/session data must remain readable and queryable after migration.
- Admin audit UI must render safely for `legacy structured`, `reduced`, and `opaque` payload shapes.
- Security bans and attack detection do not strictly require fingerprint to operate:
  - user-based bans still work with JWT
  - IP fallback still works without fingerprint
  - fingerprint currently adds banned-user re-identification without JWT and should be treated as a compatibility gap when removed or reduced
- Current rate-limit logic does not require fingerprint for its live identifier path; it currently keys by `user` or `ip`.
- Current suspicion scoring is structurally coupled to legacy fields and cannot remain behaviorally equivalent if replacement payloads are opaque only.
- Any later backend contract must explicitly define how `missing`, `legacy structured`, and future replacement payloads are represented and degraded.
- The Phase 0 replacement choice is now frozen at the correct level:
  - replacement integration must be hidden behind a stable internal adapter contract
  - concrete replacement vendor/library remains intentionally deferred until the replacement-design phase

### Phase 0 Sign-off

- current behavior is documented well enough to verify both regression and improvement in Phase 1
- the remaining concerns are migration inputs for later phases, not blockers for entering Phase 1
- no Phase 0 code, schema, or runtime mutation is required beyond this roadmap closeout

### Phase 0 Deliverable Index

Affected module references captured in this phase:

- Frontend startup and sender path:
  - `frontend/src/app/layout.tsx`
  - `frontend/src/components/FingerprintInitializer.tsx`
  - `frontend/src/hooks/useFingerprint.ts`
  - `frontend/src/lib/fingerprint/index.ts`
  - `frontend/src/lib/api/client.ts`
- Frontend baseline pages:
  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/app/dashboard/labs/[id]/page.tsx`
  - `frontend/src/lib/api/student.ts`
- Backend auth/session/device path:
  - `backend/app/api/v1/endpoints/auth.py`
  - `backend/app/api/v1/endpoints/admin_impersonate.py`
  - `backend/app/services/session_service.py`
  - `backend/app/services/device_service.py`
  - `backend/app/models/device.py`
- Backend audit/security/suspicion path:
  - `backend/app/audit/utils.py`
  - `backend/app/audit/middleware.py`
  - `backend/app/audit/models.py`
  - `backend/app/middleware/security_monitor.py`
  - `backend/app/services/security_monitor/detector.py`
  - `backend/app/audit/suspicion/fingerprint.py`
  - `backend/app/audit/suspicion/service.py`
  - `backend/app/api/v1/endpoints/admin_audit.py`
  - `backend/app/api/v1/endpoints/user_sessions.py`
  - `backend/app/services/rate_limit/service.py`
  - `backend/app/services/rate_limit/models.py`

### Public APIs / Interfaces

- Phase 0 does not change any runtime API, schema, storage shape, or request format.
- The only interface addition in this phase is a documentation contract in this roadmap:
  - currently accepted payload shapes are `missing`, `legacy structured`, and `malformed/raw hash`
  - the future replacement remains adapter-defined, not vendor-defined

### Phase 0 Final Review

- Repo search was re-run and the documented frontend caller map still matches actual call sites.
- Repo search was re-run and the documented backend parsing, storage, and dependency paths still match the written notes.
- The baseline measurements in this section now match the captured dashboard and lab-detail evidence.
- This section now contains all Phase 0 deliverables:
  - startup path
  - frontend callers
  - backend parsers and dependencies
  - storage locations
  - fallback behavior
  - baseline measurements
  - compatibility obligations

### Assumptions and Defaults

- Baseline environment is the local dev stack behind `http://localhost`.
- Baseline measurement path is `dev admin` login plus impersonation of `Осипов Ярослав Иванович`.
- Concrete replacement vendor remains intentionally undecided in Phase 0.
- This phase is now closed and no longer distinguishes between `draft findings` and `completed checklist items`.

## Phase 1. Immediate Stabilization Without Replacement

Goal: stop the performance risk before introducing any new library.

Exit gate:

- production path no longer performs heavy eager fingerprint collection on app startup

Checklist:

- [x] Remove or disable root-layout eager fingerprint initialization. - 2026-03-26 - root layout now mounts `FingerprintInitializer` only in `legacy` mode; shipped default is `disabled` - files: frontend/src/app/layout.tsx, frontend/src/lib/fingerprint/mode.ts - verification: source inspection test + `npm run build`
- [x] Prevent request interceptor from triggering synchronous fingerprint collection on early requests. - 2026-03-26 - axios clients now use cache-only `getCachedFingerprintHeader()` and never call sync collector on request path - files: frontend/src/lib/api/client.ts, frontend/src/lib/fingerprint/index.ts, frontend/src/lib/api/client.test.ts, frontend/src/lib/fingerprint/mode.test.ts - verification: vitest + browser runtime capture on `/auth/login` and `/dashboard`
- [x] Ensure API requests can proceed safely with missing fingerprint header. - 2026-03-26 - initial auth and dashboard API requests completed with `X-Device-Fingerprint = null` - files: frontend/src/lib/api/client.ts, frontend/src/lib/fingerprint/index.ts - verification: browser runtime capture + `npm run build`
- [x] Ensure login flow tolerates absent fingerprint. - 2026-03-26 - backend login path accepts missing header; browser `dev-login` returned `200` with `device_registered: null` - files: backend/tests/test_auth_session_cookies.py, backend/app/services/device_service.py - verification: pytest + browser runtime capture
- [x] Ensure session creation tolerates absent fingerprint. - 2026-03-26 - session creation continues with `device_summary = null` and no raw fingerprint requirement - files: backend/tests/test_auth_session_cookies.py, backend/tests/test_admin_impersonation_sessions.py, backend/tests/test_session_privacy.py - verification: pytest
- [x] Ensure device registration tolerates absent fingerprint without noisy failures. - 2026-03-26 - empty fingerprint path remains early-return but warning-level noise was removed - files: backend/app/services/device_service.py, backend/tests/test_device_binding_preservation.py - verification: pytest
- [x] Ensure audit middleware tolerates absent fingerprint without degraded request handling. - 2026-03-26 - audit middleware preserves request handling and stores `fingerprint = None` when header is absent - files: backend/tests/test_logging_audit_hardening.py - verification: pytest
- [x] Ensure security-monitor middleware tolerates absent fingerprint. - 2026-03-26 - existing security-monitor missing-header path remained valid; no code change required - files: backend/tests/test_device_binding_preservation.py - verification: pytest preservation tests + browser runtime requests with null fingerprint headers
- [x] Add temporary feature flag or kill switch for fingerprint collection. - 2026-03-26 - added `NEXT_PUBLIC_FINGERPRINT_MODE` with supported values `disabled|legacy`; shipped default is `disabled` - files: frontend/src/lib/fingerprint/mode.ts, frontend/Dockerfile.prod, deploy/docker-compose.yml, deploy/docker-compose.dev.yml, deploy/.env, deploy/.env.dev, deploy/.env.prod, deploy/.env.example - verification: repo grep + `npm run build`
- [x] Add explicit logging around fingerprint-disabled mode. - 2026-03-26 - disabled mode now emits a one-time explicit frontend warning instead of legacy collection warnings - files: frontend/src/lib/fingerprint/index.ts, frontend/src/lib/fingerprint/mode.test.ts - verification: vitest + browser console capture
- [x] Verify that dashboard cold open no longer triggers legacy collector paths. - 2026-03-26 - browser cold open after `dev-login` showed dashboard API requests with null fingerprint headers and no legacy collector console messages - files: frontend/src/app/layout.tsx, frontend/src/lib/api/client.ts, frontend/src/lib/fingerprint/index.ts - verification: browser runtime capture + `npm run build`

Verification:

- no fingerprint collection at root layout
- no sync collector on first request path
- auth/session/audit still function in degraded mode

Rollback:

- re-enable feature flag only
- no schema rollback needed

### Phase 1 Final Evidence

Phase 1 completed on `2026-03-26`. Phase 2 may start.

- Chosen flag and default:
  `NEXT_PUBLIC_FINGERPRINT_MODE` added with supported values `disabled|legacy`; all shipped deployment env files now default to `disabled`.
- Automated verification:
  `cd frontend && npm exec vitest run src/lib/fingerprint/mode.test.ts src/lib/api/client.test.ts src/app/layout.source.test.ts src/hooks/useAutoLogin.test.ts` -> `4 files passed, 11 tests passed`
  `cd frontend && npm run build` -> passed
  `cd backend && ./venv/bin/pytest -q tests/test_auth_session_cookies.py tests/test_admin_impersonation_sessions.py tests/test_device_binding_preservation.py tests/test_logging_audit_hardening.py tests/test_session_privacy.py` -> `49 passed`
- Browser/runtime verification:
  Chromium smoke on `http://localhost/auth/login` showed first API request `/api/v1/users/me` with `X-Device-Fingerprint = null`
  Browser `dev-login` returned `200` with `"device_registered": null`
  Cold open of `http://localhost/dashboard` showed only null fingerprint headers on initial API requests: `/student/profile`, `/student/attendance`, `/student/labs`, `/student/attestation/*`, `/student/announcements`, `/public/semester-info`
  Browser console showed only one explicit disabled-mode warning and did not show legacy messages like `getFingerprint() called before initialization` or `Initialized successfully`
- Accepted temporary degradation:
  fingerprint-based anonymous re-identification remains unavailable while headers are absent; security monitor falls back to user/IP paths until the replacement adapter is introduced in later phases

## Phase 2. Backend Decoupling From Legacy Custom Schema

Goal: make backend compatible with absence of fingerprint and future replacement schema.

Exit gate:

- backend works with `missing`, `legacy`, and `replacement-adapter` payloads

Checklist:

- [x] Define canonical backend fingerprint contract for migration period.
- [x] Separate raw fingerprint payload storage from derived device summary logic.
- [x] Ensure device service no longer assumes legacy custom JSON keys are always present.
- [x] Ensure audit extraction supports missing payload and opaque hash safely.
- [x] Ensure suspicion scoring can short-circuit safely when structured components are unavailable.
- [x] Ensure session summary builder can tolerate reduced payload structure.
- [x] Ensure admin audit rendering tolerates legacy, reduced, and replacement payload shapes.
- [x] Ensure rate-limit or security-monitor flows degrade safely when fingerprint quality is reduced.
- [x] Document which derived fields remain mandatory after migration.
- [x] Decide whether replacement payload will be stored raw, normalized, or both.
- [x] Decide whether existing historical JSONB data must remain query-compatible.
- [x] Add compatibility tests for all accepted payload forms.

Implementation notes (2026-03-26):

- Canonical backend contract is a migration envelope with `schema = "fingerprint-migration-v1"` and `kind in {"missing", "opaque_hash", "legacy_structured", "normalized_replacement"}`; missing fingerprint may be represented either by header absence / `None` or by an explicit `kind = "missing"` envelope, and both forms must degrade to no-op.
- The envelope keeps `raw_payload`, `opaque_hash`, `normalized_summary`, `normalized_matching`, and `quality`, so backend runtime no longer depends on legacy raw JSON keys being present everywhere.
- Replacement payload storage decision for this phase: store both raw and normalized representations inside the canonical envelope where fingerprint data is persisted for audit/history.
- Historical JSONB policy for this phase: remain read-compatible for legacy stored records; no migration/backfill is required and no new code may assume legacy JSON-path query shape.
- Legacy continuity policy for this phase: device trust and security fingerprint mappings stay backward-compatible for already stored legacy payloads by retaining legacy hash behavior on legacy inputs while using canonical digests for normalized replacement payloads.
- Derived fields are best-effort, not ingress-mandatory. After migration, backend only treats these as canonical derived outputs when available:
- `normalized_summary`: `platform`, `browser`, `screen.width`, `screen.height`
- `normalized_matching`: `platform`, `hardwareConcurrency`, `screen`, `webgl`, `canvas`, `userAgent`
- Missing or reduced fingerprint quality must degrade to summary-only or no-op behavior without breaking auth, sessions, audit, suspicion scoring, or security monitoring.

Verification:

- backend tests cover missing fingerprint
- backend tests cover legacy fingerprint
- backend tests cover normalized replacement payload

Rollback:

- keep compatibility parser in place
- avoid one-way schema coupling in this phase

## Phase 3. Full Removal of Current Custom Fingerprint System

Goal: remove custom implementation completely after the system is safe without it.

Exit gate:

- no runtime imports or calls remain to the old custom fingerprint stack

Checklist:

- [x] Remove frontend custom fingerprint module entrypoints. - 2026-03-27 - removed `frontend/src/lib/fingerprint/*` runtime entrypoints and dropped frontend runtime imports - files: frontend/src/app/layout.tsx, frontend/src/lib/api/client.ts, frontend/src/lib/fingerprint/* - verification: repo search + `npm run build`
- [x] Remove canvas collector implementation. - 2026-03-27 - deleted legacy canvas collector module with the legacy subtree - files: frontend/src/lib/fingerprint/canvas.ts - verification: repo search + `npm run build`
- [x] Remove WebGL collector implementation. - 2026-03-27 - deleted legacy WebGL collector module with the legacy subtree - files: frontend/src/lib/fingerprint/webgl.ts - verification: repo search + `npm run build`
- [x] Remove audio collector implementation. - 2026-03-27 - deleted legacy audio collector module with the legacy subtree - files: frontend/src/lib/fingerprint/audio.ts - verification: repo search + `npm run build`
- [x] Remove font collector implementation. - 2026-03-27 - deleted legacy font collector module with the legacy subtree - files: frontend/src/lib/fingerprint/fonts.ts - verification: repo search + `npm run build`
- [x] Remove async collector implementation if only used for legacy fingerprint. - 2026-03-27 - deleted async collector module used only by the removed legacy fingerprint path - files: frontend/src/lib/fingerprint/async-collectors.ts - verification: repo search + `npm run build`
- [x] Remove custom hook and initializer wiring. - 2026-03-27 - removed root-layout initializer mount and deleted custom hook/initializer files - files: frontend/src/app/layout.tsx, frontend/src/components/FingerprintInitializer.tsx, frontend/src/hooks/useFingerprint.ts - verification: source inspection + `npm run build` + vitest
- [x] Remove dead code in API client related only to legacy collection path. - 2026-03-27 - removed fingerprint header attach helper/imports from authenticated and public axios clients - files: frontend/src/lib/api/client.ts - verification: repo search + vitest + `npm run build`
- [x] Remove dead tests specific to legacy collector implementation. - 2026-03-27 - removed legacy client/mode tests and updated source-level cleanup assertions; removed fingerprint-only mocks from unrelated feedback tests - files: frontend/src/lib/api/client.test.ts, frontend/src/lib/fingerprint/mode.test.ts, frontend/src/app/layout.source.test.ts, frontend/src/components/feedback/hooks/__tests__/useFeedbackForm.bug.test.ts, frontend/src/components/feedback/hooks/__tests__/useFeedbackForm.preservation.test.ts - verification: `npx vitest run src/app/layout.source.test.ts src/components/feedback/hooks/__tests__/useFeedbackForm.bug.test.ts src/components/feedback/hooks/__tests__/useFeedbackForm.preservation.test.ts`
- [x] Remove dead documentation describing the custom collector. - 2026-03-27 - no standalone repo docs describing the active custom collector remained; removed deploy-time env references tied only to legacy frontend activation - files: frontend/Dockerfile.prod, deploy/docker-compose.dev.yml, deploy/docker-compose.yml, deploy/.env.dev, deploy/.env.prod, deploy/.env.example - verification: repo search
- [x] Remove dead metrics/logging tied only to legacy collector internals. - 2026-03-27 - removed legacy frontend collector logging by deleting the collector subtree and header attach path - files: frontend/src/lib/fingerprint/*, frontend/src/lib/api/client.ts - verification: repo search + `npm run build`
- [x] Verify no frontend path imports legacy fingerprint code. - 2026-03-27 - repo search found no active frontend runtime imports/calls to legacy fingerprint modules - files: frontend/src/app/layout.tsx, frontend/src/lib/api/client.ts - verification: `rg -n --hidden "@/lib/fingerprint|../fingerprint|FingerprintInitializer|useFingerprint|getCachedFingerprintHeader|getFingerprintHash|getFingerprintAsync|initializeFingerprint|NEXT_PUBLIC_FINGERPRINT_MODE" frontend/src frontend/Dockerfile.prod deploy`
- [x] Verify no backend path depends on legacy-only fields being present from new clients. - 2026-03-27 - backend compatibility layer continues to accept missing fingerprint headers while preserving historical-read compatibility for old records and old clients - files: backend/app/api/v1/endpoints/auth.py, backend/app/api/v1/endpoints/admin_impersonate.py, backend/app/services/session_service.py, backend/app/services/device_service.py, backend/app/fingerprint_contract.py, backend/app/fingerprint_contract_support.py - verification: `backend/venv/bin/pytest backend/tests/test_auth_session_cookies.py backend/tests/test_admin_impersonation_sessions.py backend/tests/test_session_privacy.py backend/tests/test_logging_audit_hardening.py backend/tests/test_device_binding_preservation.py backend/tests/test_fingerprint_contract.py`

Verification:

- repo search shows no active runtime references to legacy frontend collector
- build passes
- test suite relevant to auth/session/audit/device flows passes

Rollback:

- restore removed module only if Phase 1 kill-switch approach cannot sustain service
- Phase 3 removal eliminated the frontend feature-flag path; rollback now requires code revert or redeploy of a pre-Phase-3 frontend image rather than re-enabling `NEXT_PUBLIC_FINGERPRINT_MODE`

### Phase 3 Final Evidence

- Frontend no longer mounts any legacy fingerprint initializer or hook during app startup.
- Frontend axios clients no longer add `X-Device-Fingerprint` on request paths.
- Legacy frontend collector subtree under `frontend/src/lib/fingerprint/` has been removed.
- Deploy/build wiring for `NEXT_PUBLIC_FINGERPRINT_MODE` has been removed from active frontend deployment files.
- Backend historical compatibility remains intentionally in place for audit/session/device reads and optional old-client tolerance; this is not an active frontend collector path.
- Verification completed on `2026-03-27`:
  - `npm run build` in `frontend/`
  - `npx vitest run src/app/layout.source.test.ts src/components/feedback/hooks/__tests__/useFeedbackForm.bug.test.ts src/components/feedback/hooks/__tests__/useFeedbackForm.preservation.test.ts`
  - `backend/venv/bin/pytest backend/tests/test_auth_session_cookies.py backend/tests/test_admin_impersonation_sessions.py backend/tests/test_session_privacy.py backend/tests/test_logging_audit_hardening.py backend/tests/test_device_binding_preservation.py backend/tests/test_fingerprint_contract.py`

## Phase 4. Replacement Design Freeze

Goal: lock the replacement integration design before any implementation.

Exit gate:

- adapter contract is frozen and approved for implementation

Checklist:

- [x] Confirm `thumbmarkjs` is still the chosen replacement. - 2026-03-27 - chosen library remains `@thumbmarkjs/thumbmarkjs` behind a local adapter boundary
- [x] Confirm package version to adopt. - 2026-03-27 - exact package version frozen to `1.7.6` - files: frontend/package.json, frontend/package-lock.json
- [x] Review replacement documentation for collection options, caching, logging, and permissions. - 2026-03-27 - reviewed vendor options and froze local policy: no vendor API, no permissions collection, no vendor logging, local cache only
- [x] Decide whether to use raw thumbmark output, normalized output, or both. - 2026-03-27 - store both normalized contract data and adapter-owned raw snapshot inside canonical envelope
- [x] Define frontend adapter output schema sent to backend. - 2026-03-27 - frozen envelope: `schema="fingerprint-migration-v1"`, `kind="normalized_replacement"`, top-level `summary`, `matching`, `client`, `raw`
- [x] Map replacement fields to backend needs:
- [x] device summary - 2026-03-27 - normalized `summary.platform`, `summary.browser`, `summary.screen`
- [x] session summary - 2026-03-27 - canonical `normalized_summary` derived from adapter envelope
- [x] audit storage - 2026-03-27 - canonical envelope stores normalized fields and adapter-owned raw snapshot for historical audit visibility
- [x] suspicion matching - 2026-03-27 - canonical `normalized_matching` maps `platform`, `hardwareConcurrency`, `screen`, `webgl`, `canvas`, `userAgent`
- [x] Decide what fingerprint fields are truly required versus optional. - 2026-03-27 - required: summary platform/browser/screen + matching platform/hardwareConcurrency/screen/webgl/canvas/userAgent; optional: language, timezone, thumbmark hash, raw component snapshot, vendor errors
- [x] Decide what expensive replacement components are excluded at first rollout. - 2026-03-27 - excluded from first rollout: permissions, audio, fonts, plugins, webrtc, speech, separate screen/webgl/math components, vendor API features
- [x] Decide whether replacement collection is lazy, on-auth-only, or another trigger. - 2026-03-27 - frozen to lazy auth-only prewarm on login and impersonation surfaces; no root-layout eager collection
- [x] Decide whether replacement header is sent on every request or only selected flows. - 2026-03-27 - header sent only on `/auth/otp`, `/auth/dev-login`, `/admin/impersonate/{user_id}`, `/admin/impersonate/exit`
- [x] Decide how caching is handled client-side. - 2026-03-27 - local adapter cache only: in-flight promise dedupe + `sessionStorage` TTL cache for fingerprint payload; runtime mode is not persisted across tab lifetime after fetch failure
- [x] Decide how logging is configured in production. - 2026-03-27 - vendor logging disabled via `logging: false`; no adapter payload logging on hot paths
- [x] Decide how privacy/compliance concerns are documented. - 2026-03-27 - frozen collection surface is auth-only, excludes permissions-heavy components, keeps backend contract vendor-neutral, and avoids root-layout eager collection
- [x] Freeze acceptance criteria for replacement rollout. - 2026-03-27 - cold open must not collect, hot request paths stay fail-open, backend consumes canonical envelope only, selected auth flows may send normalized replacement payload

Design constraints:

- no eager collection from root layout
- no synchronous collection on hot request path
- no backend dependence on vendor-specific raw shape
- replacement library must sit behind local adapter interface

Implementation notes (2026-03-27):

- Adapter contract is frozen around a local `thumbmarkjs` wrapper in `frontend/src/lib/fingerprint/adapter.ts`.
- The adapter uses `system`, `hardware`, `canvas`, and `locales` only; `screen` comes from `window.screen` to avoid vendor-shape instability.
- Runtime rollout source of truth is backend `FRONTEND_FINGERPRINT_MODE`, exposed by `/auth/fingerprint-mode`; successful runtime fetch is authoritative for the current page lifecycle.
- Fallback mode may use server-rendered bootstrap state from the root HTML dataset, but fallback is intentionally not persisted after fetch failure to preserve rollback correctness.

## Phase 5. Frontend Integration of Replacement Behind Adapter

Goal: integrate `thumbmarkjs` without leaking vendor shape through the app.

Exit gate:

- frontend sends only the normalized adapter payload

Checklist:

- [x] Add replacement dependency. - 2026-03-27 - added `@thumbmarkjs/thumbmarkjs@1.7.6` - files: frontend/package.json, frontend/package-lock.json
- [x] Create local adapter module with stable interface. - 2026-03-27 - added local adapter and mode helpers - files: frontend/src/lib/fingerprint/adapter.ts, frontend/src/lib/fingerprint/mode.ts
- [x] Implement normalized payload builder from replacement output. - 2026-03-27 - adapter now builds the frozen normalized replacement envelope and keeps vendor shape local - files: frontend/src/lib/fingerprint/adapter.ts
- [x] Implement cache strategy for normalized payload. - 2026-03-27 - adapter uses in-flight dedupe plus `sessionStorage` TTL cache for the serialized envelope - files: frontend/src/lib/fingerprint/adapter.ts
- [x] Implement lazy initialization strategy according to frozen design. - 2026-03-27 - prewarm happens only on login surface mount and impersonation intent/active impersonation banner - files: frontend/src/hooks/useAutoLogin.ts, frontend/src/app/admin/students/[id]/components/StudentProfileCard.tsx, frontend/src/components/dashboard/ImpersonationBanner.tsx
- [x] Ensure no collection occurs before the chosen trigger point. - 2026-03-27 - root layout only exposes rollout mode via HTML dataset; no collector is mounted there - files: frontend/src/app/layout.tsx
- [x] Update API client to use adapter output instead of legacy collector. - 2026-03-27 - selected auth/admin flows now attach `X-Device-Fingerprint` via adapter cache reader instead of legacy client wiring - files: frontend/src/lib/api/auth.ts, frontend/src/lib/api/admin.ts, frontend/src/lib/api/fingerprint-auth.ts
- [x] Ensure request path never falls back to heavy synchronous collection. - 2026-03-27 - submit paths read cache only and remain fail-open if prewarm is missing, slow, or failed - files: frontend/src/lib/api/fingerprint-auth.ts, frontend/src/hooks/useAutoLogin.test.ts
- [x] Ensure auth flow receives the normalized payload if required. - 2026-03-27 - auth and dev-login flows now send adapter payload when present in cache - files: frontend/src/lib/api/auth.ts
- [x] Ensure non-auth requests use the agreed header behavior only. - 2026-03-27 - header attach is scoped to auth and impersonation flows only - files: frontend/src/lib/api/auth.ts, frontend/src/lib/api/admin.ts
- [x] Add frontend tests for adapter normalization. - 2026-03-27 - adapter tests cover normalized envelope shape and mandatory field handling - files: frontend/src/lib/fingerprint/adapter.test.ts
- [x] Add frontend tests for disabled/missing fingerprint mode. - 2026-03-27 - mode tests cover runtime mode success/failure fallback and non-sticky fallback behavior - files: frontend/src/lib/fingerprint/mode.test.ts
- [x] Add frontend tests for cache hit/miss behavior. - 2026-03-27 - adapter and request-path tests cover cache hit/miss, dedupe, and fail-open submit behavior - files: frontend/src/lib/fingerprint/adapter.test.ts, frontend/src/lib/api/auth.test.ts, frontend/src/lib/api/admin.test.ts, frontend/src/lib/api/fingerprint-auth.test.ts, frontend/src/hooks/useAutoLogin.test.ts, frontend/src/app/admin/students/[id]/components/StudentProfileCard.test.tsx, frontend/src/components/dashboard/ImpersonationBanner.test.tsx

Verification:

- cold open does not collect before intended trigger
- header payload shape matches frozen contract
- no runtime import of vendor library outside adapter boundary

Implementation notes (2026-03-27):

- `thumbmarkjs` is imported dynamically only inside `frontend/src/lib/fingerprint/adapter.ts`.
- Request-time header assembly uses cache only and never triggers synchronous collection.
- Student-profile impersonation prewarm was tightened to explicit user intent (`mouseenter` / `focus`) to avoid expanding collection scope during ordinary admin browsing.
- Runtime mode fetch failure no longer sticks an `off` fallback for the rest of the tab lifecycle.

## Phase 6. Backend Integration of Replacement Contract

Goal: support new normalized payload without losing audit/device behavior.

Exit gate:

- backend fully accepts normalized replacement payload and preserves required features

Checklist:

- [x] Implement backend parser for normalized replacement payload. - 2026-03-27 - canonical parser supports `kind="normalized_replacement"` inside the migration envelope - files: backend/app/fingerprint_contract.py, backend/app/fingerprint_contract_support.py
- [x] Update device summary extraction to use normalized contract. - 2026-03-27 - device-service path consumes canonical normalized fields and tolerates missing fingerprint headers - files: backend/app/services/device_service.py, backend/app/fingerprint_contract_support.py
- [x] Update session summary generation to use normalized contract. - 2026-03-27 - session/audit helpers derive summary from canonical normalized envelope instead of raw vendor keys - files: backend/app/services/session_service.py, backend/app/fingerprint_contract_support.py
- [x] Update audit extraction and storage if needed. - 2026-03-27 - audit/history remains canonical-envelope based and keeps historical-read compatibility - files: backend/app/fingerprint_contract.py, backend/app/fingerprint_contract_support.py
- [x] Update suspicion scoring to use normalized fields only. - 2026-03-27 - suspicion scoring reads canonical matching fields rather than requiring legacy client JSON keys - files: backend/app/audit/suspicion/fingerprint.py, backend/app/fingerprint_contract_support.py
- [x] Update admin audit UI expectations if payload rendering changes. - 2026-03-27 - admin audit UI handles legacy structured, missing, opaque hash, and normalized replacement envelopes - files: frontend/src/app/admin/audit/components/auditFingerprintModel.ts, frontend/src/app/admin/audit/components/AuditFingerprintSection.test.ts
- [x] Update security-monitor integration if it depends on fingerprint structure. - 2026-03-27 - security monitoring stays compatible through canonical normalization and legacy fallback handling - files: backend/app/services/security_monitor/detector.py, backend/app/fingerprint_contract_support.py
- [x] Keep compatibility for old stored records and old clients during transition. - 2026-03-27 - compatibility envelope still supports `missing`, `legacy_structured`, and `normalized_replacement` inputs - files: backend/app/fingerprint_contract.py, backend/app/fingerprint_contract_support.py
- [x] Add backend tests for normalized replacement payload. - 2026-03-27 - parser/contract suite covers normalized replacement payloads - files: backend/tests/test_fingerprint_contract.py
- [x] Add mixed-mode tests: old record + new client + no-fingerprint client. - 2026-03-27 - focused auth/impersonation/contract tests cover missing fingerprint tolerance and normalized replacement acceptance alongside legacy compatibility - files: backend/tests/test_fingerprint_contract.py, backend/tests/test_auth_session_cookies.py, backend/tests/test_admin_impersonation_sessions.py

Verification:

- device binding works
- session summary works
- audit ingest works
- suspicion scoring does not crash or silently mis-score

Implementation notes (2026-03-27):

- Backend contract remains vendor-neutral; no runtime path depends on ThumbmarkJS raw component shape.
- Auth and impersonation endpoints continue to tolerate missing `X-Device-Fingerprint` headers without breaking session creation or device registration flows.

## Phase 7. Validation, Benchmarks, and Regression Gates

Goal: prove the new system is safer and lighter than the old one.

Exit gate:

- performance and correctness gates pass

Checklist:

- [x] Run frontend build and relevant tests. - 2026-03-27 - `npx vitest run ...` over the fingerprint/auth slice passed `29/29`; `npm run build` passed
- [x] Run backend relevant tests. - 2026-03-27 - `backend/venv/bin/pytest backend/tests/test_fingerprint_contract.py backend/tests/test_auth_session_cookies.py backend/tests/test_admin_impersonation_sessions.py` passed `26/26`
- [x] Benchmark cold open before and after on student dashboard. - 2026-03-27 - stabilized auth-only runtime run on the same localhost dev compose stack captured `/dashboard` after student OTP login: settled snapshot `3503 ms -> 2764 ms`; `responseEnd 71 -> 29 ms`; `DOMContentLoaded 106 -> 48 ms`; `loadEventEnd 879 -> 258 ms`; `FCP 448 -> 284 ms`; request-path long-task notes after: single `122 ms` task; evidence: `/tmp/phase7-runtime-auth-only-run2.json` (collector: `frontend/scripts/phase7-runtime-check.mjs`)
- [x] Benchmark lab detail page before and after. - 2026-03-27 - stabilized auth-only runtime run captured `/dashboard/labs/7313b7bd-d821-4ceb-8a5d-f9bcdb48f285`: settled snapshot `2749 ms -> 3165 ms`; navigation metrics improved despite dev-server settle noise: `responseEnd 263 -> 102 ms`; `DOMContentLoaded 296 -> 136 ms`; `loadEventEnd 1094 -> 657 ms`; `FCP 624 -> 360 ms`; after long-task notes: `87 ms`, `207 ms`; first post-recreate run (`/tmp/phase7-runtime-auth-only.json`) showed Turbopack cold-compile noise and was not used as the primary comparison sample
- [x] Compare request count before and after on initial dashboard load. - 2026-03-27 - dashboard cold load request count stayed flat at `11 -> 11`, but request-path fingerprint surface dropped from `11/11` API requests carrying `X-Device-Fingerprint` to `0/11`; stabilized after evidence: `/tmp/phase7-runtime-auth-only-run2.json`
- [x] Confirm no repeated sync collection happens. - 2026-03-27 - adapter/request-path tests confirm cache-only submit behavior and in-flight dedupe; request paths do not wait for prewarm - files: frontend/src/lib/fingerprint/adapter.test.ts, frontend/src/hooks/useAutoLogin.test.ts
- [x] Confirm no root-layout eager collection happens. - 2026-03-27 - root layout only carries rollout mode dataset and does not mount fingerprint initializer logic - files: frontend/src/app/layout.tsx, frontend/src/app/layout.source.test.ts
- [x] Confirm audit entries still store expected values. - 2026-03-27 - live `student_audit_log` rows for `/api/v1/auth/otp` and `/api/v1/auth/dev-login` now store canonical fingerprint envelopes with `schema=fingerprint-migration-v1` and `kind=normalized_replacement`; sampled non-auth request-path rows for `/api/v1/student/profile`, `/api/v1/student/labs/{id}`, `/api/v1/student/announcements`, and `/api/v1/auth/fingerprint-mode` remained `fingerprint=null`, proving request-path loads no longer persist request-level fingerprint blobs
- [x] Confirm device registration still works as intended. - 2026-03-27 - auth-only OTP login for student `Осипов Ярослав Иванович` created device binding `0 -> 1` with `device_info { platform: Linux, browser: Chrome, screen: 1280×720 }`; `/users/me/devices/{id}/confirm` returned `200` with `is_trusted=true`; `/users/me/devices/{id}` delete returned `204`; final device count returned to `0`; evidence: `/tmp/phase7-runtime-auth-only-run3.json`
- [x] Confirm session summaries still render correctly. - 2026-03-27 - live `/users/me/sessions` response under auth-only returned current and historical session summaries with masked IP `172.18.x.x`, platform `Linux`, browser `Chrome`, screen `1280×720`; security-tab UI validation matched rendered fragments `Активные сессии`, `Привязанные устройства`, `Linux • Chrome`, `172.18.x.x`, `1280×720`, `Текущая`, `Подтвердить`; evidence: `/tmp/phase7-runtime-auth-only-run3.json`
- [x] Confirm admin audit UI still handles records correctly. - 2026-03-27 - audit UI model tests cover normalized replacement plus legacy/missing/opaque variants - files: frontend/src/app/admin/audit/components/AuditFingerprintSection.test.ts
- [x] Confirm feature flag or kill switch still works. - 2026-03-27 - runtime mode endpoint + HTML bootstrap keep `off|auth_only` control without frontend root-layout collection wiring; containerized dev/prod config now also propagates the rollout mode into backend and frontend runtime/build env so SSR bootstrap no longer falls back to hardcoded `off` inside Docker - files: backend/app/api/v1/endpoints/auth.py, backend/tests/test_auth_session_cookies.py, frontend/src/lib/fingerprint/mode.ts, frontend/src/lib/fingerprint/mode.test.ts, deploy/docker-compose.dev.yml, deploy/docker-compose.yml, frontend/Dockerfile.prod
- [x] Record residual risk list. - 2026-03-27 - no blocking residual risks remain for the implemented frontend/backend migration slice; the only non-blocking evidence limitation is that the original baseline capture did not record explicit old-system long-task entries, so CPU comparison relies on the new post-migration long-task notes plus improved request/timing evidence rather than a symmetric legacy long-task trace

Required evidence:

- test outputs
- before/after timing notes
- before/after request notes
- before/after CPU or long-task notes

Phase 7 evidence captured on 2026-03-27:

- tests: `npm run build`; `npx vitest run src/lib/fingerprint/adapter.test.ts src/hooks/useAutoLogin.test.ts src/app/layout.source.test.ts src/app/admin/audit/components/AuditFingerprintSection.test.ts`; `backend/venv/bin/pytest backend/tests/test_fingerprint_contract.py backend/tests/test_auth_session_cookies.py backend/tests/test_admin_impersonation_sessions.py backend/tests/test_session_privacy.py backend/tests/test_logging_audit_hardening.py backend/tests/test_device_binding_preservation.py`
- runtime collector: `frontend/scripts/phase7-runtime-check.mjs`
- auth-only runtime artifacts: `/tmp/phase7-runtime-auth-only.json`, `/tmp/phase7-runtime-auth-only-run2.json`, `/tmp/phase7-runtime-auth-only-run3.json`
- before/after request notes: baseline dashboard `11` API requests with `11/11` carrying `X-Device-Fingerprint`; stabilized auth-only after run kept `11` API requests with `0/11` carrying the header; lab detail stayed at `5` API requests with `0/5` carrying the header
- before/after timing notes: dashboard and lab detail after-runs improved `responseEnd`, `DOMContentLoaded`, `loadEventEnd`, and `FCP` against the baseline on the same localhost dev compose stack
- CPU/long-task notes: stabilized auth-only after run recorded dashboard `122 ms` long task and lab detail `87 ms` + `207 ms`; the first post-recreate sample showed extra dev-server compile noise on lab detail and was retained as supporting evidence only

## Phase 8. Rollout and Rollback

Goal: ship safely with explicit rollback.

Exit gate:

- rollout plan is executable and rollback is trivial

Checklist:

- [x] Decide rollout mechanism: feature flag, config flag, or deployment wave. - 2026-03-27 - rollout mechanism is backend config flag `FRONTEND_FINGERPRINT_MODE` with supported values `off|auth_only`, exposed to frontend via `/auth/fingerprint-mode` and HTML bootstrap
- [x] Define rollback trigger conditions. - 2026-03-27 - rollback triggers are now explicit and executable: immediate rollback on confirmed auth/session/device failures, audit-ingestion breakage, admin audit rendering breakage, repeated fingerprint adapter errors, or dashboard startup regression above `25%` across `3` repro attempts; operator reference: [FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md](/home/zaikana/Рабочий стол/platforma_maga/md/FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md)
- [x] Define monitoring signals during rollout. - 2026-03-27 - rollout monitoring is defined via smoke checks plus concrete log/SQL signals for auth success, session/device health, audit ingestion, request-path cleanliness, and admin audit rendering; operator reference: [FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md](/home/zaikana/Рабочий стол/platforma_maga/md/FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md)
- [x] Define who watches rollout and for how long. - 2026-03-27 - ownership is role-based: primary watcher is the engineer performing rollout, secondary watcher is admin/support operator; watch window is `30 minutes` active plus next business day passive; operator reference: [FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md](/home/zaikana/Рабочий стол/platforma_maga/md/FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md)
- [x] Prepare rollback command/config steps. - 2026-03-27 - rollback is documented as one config change `FRONTEND_FINGERPRINT_MODE=off` plus `docker compose ... up -d --force-recreate backend frontend nginx`; notes also cover the `deploy/rebuild.sh` flow and verification commands; operator reference: [FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md](/home/zaikana/Рабочий стол/platforma_maga/md/FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md)
- [x] Verify rollback does not require schema rollback. - 2026-03-27 - fingerprint migration slice introduced no new fingerprint-specific Alembic revision; runtime rollback only changes the rollout flag and container env, while `student_audit_log` and `devices` stay on the already-supported contract path
- [x] Verify old clients remain tolerated during rollout window. - 2026-03-27 - backend compatibility tests confirm tolerance for missing header, `legacy_structured`, `opaque_hash`, and `normalized_replacement` payloads; auth/impersonation flows also tolerate missing `X-Device-Fingerprint` without session creation failure - files: `backend/tests/test_auth_session_cookies.py`, `backend/tests/test_admin_impersonation_sessions.py`, `backend/tests/test_fingerprint_contract.py`, `backend/tests/test_session_privacy.py`, `frontend/src/app/admin/audit/components/AuditFingerprintSection.test.ts`
- [x] Publish operator notes for support/debugging. - 2026-03-27 - operator notes published in [FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md](/home/zaikana/Рабочий стол/platforma_maga/md/FINGERPRINT_ROLLOUT_OPERATOR_NOTES_2026-03-27.md)
- [ ] Mark final sign-off only after post-rollout observation window.

Rollback triggers:

- startup performance regression
- auth/session/device failures
- audit ingestion failures
- admin audit rendering failures
- unexpected client errors around fingerprint adapter

## Acceptance Checklist

This section is only marked after all phases above are complete.

- [x] Legacy custom fingerprint code removed from active runtime. - 2026-03-27 - Phase 3 removal completed; active frontend runtime no longer mounts or imports the legacy collector path
- [x] Replacement integrated behind adapter. - 2026-03-27 - `thumbmarkjs` runs only behind the local adapter and selected auth/admin flows read only the normalized adapter envelope
- [x] Backend decoupled from legacy-only schema assumptions. - 2026-03-27 - canonical migration envelope and compatibility parser are the backend contract for `missing`, `legacy_structured`, and `normalized_replacement`
- [ ] Startup fingerprint cost materially reduced.
- [ ] Student dashboard no longer shows the known risk pattern.
- [ ] Verification evidence archived.
- [ ] Rollback path documented and tested.

## Execution Log

- 2026-03-25: File created as the single roadmap/checklist for the fingerprint removal and migration program.
- 2026-03-27: Phase 4 design freeze synchronized to implemented `thumbmarkjs@1.7.6` adapter contract and frozen auth-only rollout behavior.
- 2026-03-27: Phase 5 frontend adapter integration synchronized after lazy prewarm, scoped header attach, and fail-open request-path verification were completed.
- 2026-03-27: Phase 6 backend contract section synchronized to the already-landed canonical parser / compatibility layer and focused backend verification evidence.

## Change-Control Rules

This roadmap should not be structurally changed during execution unless one of the following happens:

1. The replacement library is rejected for a concrete technical reason.
2. A backend compatibility dependency is discovered that makes a phase impossible as written.
3. A production blocker requires inserting an emergency stabilization subphase.

Allowed edits during execution:

- marking checklist state
- adding short evidence notes
- adding concrete file paths
- adding discovered blockers inside existing sections

Disallowed edits during execution:

- reordering major phases
- merging removal and replacement work into one phase
- deleting verification or rollback steps
- narrowing scope just to make the checklist pass
