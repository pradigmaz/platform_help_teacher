# Fingerprint Rollout Operator Notes

Дата: 2026-03-27

Статус: prepared for rollout

Цель: выкатить auth-only fingerprint safely and make rollback one config change plus container recreate.

Этот runbook написан для production host `platform-edu.ru`. Для другого окружения подставьте свой домен и свой `deploy/.env*`.

## 1. Rollout Switch

Единственный rollout switch:

- `FRONTEND_FINGERPRINT_MODE=off`
- `FRONTEND_FINGERPRINT_MODE=auth_only`

Источники истины в runtime:

- backend endpoint `GET /api/v1/auth/fingerprint-mode`
- frontend HTML bootstrap `data-fingerprint-mode` on `<html>`

Поддерживаемые значения сейчас только:

- `off`
- `auth_only`

Любое другое значение нормализуется в `off`.

## 2. Preconditions

Перед rollout должны быть выполнены:

- relevant frontend/backend tests green
- Phase 7 runtime evidence archived
- operator has shell access to deployment host
- operator can open student auth flow and admin audit UI

## 3. Rollout Steps

### 3.1. Preflight

Проверить текущее значение режима:

```bash
curl -s https://platform-edu.ru/api/v1/auth/fingerprint-mode
```

Проверить HTML bootstrap:

```bash
python - <<'PY'
import re, urllib.request
html = urllib.request.urlopen('https://platform-edu.ru/auth/login').read().decode('utf-8', 'ignore')
match = re.search(r'data-fingerprint-mode="([^"]+)"', html)
print(match.group(1) if match else 'NONE')
PY
```

Проверить, что backend/frontend healthy:

```bash
docker compose -f deploy/docker-compose.yml ps
```

### 3.2. Enable auth-only rollout

1. На сервере в `deploy/.env` установить:

```bash
FRONTEND_FINGERPRINT_MODE=auth_only
```

2. Применить config change без schema rollback:

```bash
docker compose -f deploy/docker-compose.yml up -d --force-recreate backend frontend nginx
```

Если используется стандартный rebuild flow:

```bash
cd deploy
./rebuild.sh
```

3. Подтвердить rollout:

```bash
curl -s https://platform-edu.ru/api/v1/auth/fingerprint-mode
```

Ожидается:

```json
{"mode":"auth_only"}
```

## 4. Active Smoke Checks

Выполнить сразу после rollout:

1. Student login:
   ожидается успешный login, dashboard opens, no request-path breakage.
2. Admin impersonation:
   ожидается successful impersonation and successful exit.
3. Security tab:
   `Sessions` and `Devices` sections load.
4. Admin audit UI:
   page opens, detail dialog renders fresh auth record.

Rollback обязателен, если любой из этих smoke checks не проходит два раза подряд.

## 5. Monitoring Signals

Во время active watch window отслеживать:

- auth success:
  student login, admin impersonation, impersonation exit remain successful
- session/device health:
  `/users/me/sessions` and `/users/me/devices` still respond and render
- audit ingestion:
  fresh `/api/v1/auth/otp` or `/api/v1/auth/dev-login` rows appear with canonical fingerprint envelope
- request-path cleanliness:
  dashboard and lab-detail requests do not reintroduce request-wide fingerprint attach
- admin audit rendering:
  admin audit page still opens and detail view handles fresh normalized records
- frontend runtime errors:
  no repeated thumbmark/fingerprint adapter errors in frontend logs

Useful checks:

```bash
docker logs edu-frontend-prod --since=15m | rg -i 'fingerprint|thumbmark|error|exception'
```

```bash
docker logs edu-backend-prod --since=15m | rg -i 'fingerprint|audit|device|exception|traceback'
```

```bash
docker exec edu-db-prod psql -U admin -d edu_platform -Atc "
select path, count(*)
from student_audit_log
where created_at > now() - interval '15 minutes'
  and fingerprint is not null
group by path
order by count(*) desc;
"
```

Expected interpretation:

- auth routes may show fingerprinted rows
- non-auth dashboard request paths should not start appearing here as new fingerprint-heavy audit rows

## 6. Rollback Triggers

Rollback must happen immediately if at least one of the following is confirmed:

- startup performance regression:
  dashboard cold-open becomes slower by more than 25% across 3 repro attempts and the regression correlates with fingerprint rollout
- auth/session/device failure:
  student login, impersonation, exit, session list, or device list fails twice consecutively after rollout
- audit ingestion failure:
  fresh auth records stop appearing or appear with malformed/missing canonical fingerprint envelope
- admin audit rendering failure:
  admin audit page or detail dialog cannot render fresh fingerprinted auth records
- unexpected frontend client errors:
  repeated thumbmark/fingerprint adapter errors appear in frontend logs or browser console during login flow

## 7. Rollback Steps

Rollback does not require DB schema rollback.

1. Set:

```bash
FRONTEND_FINGERPRINT_MODE=off
```

2. Recreate services:

```bash
docker compose -f deploy/docker-compose.yml up -d --force-recreate backend frontend nginx
```

Альтернативно можно использовать тот же standard rebuild flow после изменения `deploy/.env`:

```bash
cd deploy
./rebuild.sh
```

3. Verify:

```bash
curl -s https://platform-edu.ru/api/v1/auth/fingerprint-mode
```

Expected:

```json
{"mode":"off"}
```

4. Verify HTML bootstrap returns to `off`.

5. Repeat the same smoke checks from section 4.

## 8. Why Rollback Is Trivial

Rollback is config-only because this migration slice:

- does not introduce a new fingerprint-specific Alembic migration
- keeps existing `student_audit_log` and `devices` tables
- tolerates missing header input on auth/impersonation paths
- tolerates old payload shapes during the rollout window

## 9. Old-Client Tolerance

Old clients remain tolerated during rollout because backend contract and tests already accept:

- missing fingerprint header
- legacy structured payload
- opaque/hash-only payload
- normalized replacement payload

Relevant regression coverage:

- `backend/tests/test_auth_session_cookies.py`
- `backend/tests/test_admin_impersonation_sessions.py`
- `backend/tests/test_fingerprint_contract.py`
- `backend/tests/test_session_privacy.py`
- `frontend/src/app/admin/audit/components/AuditFingerprintSection.test.ts`

## 10. Who Watches Rollout

Role ownership during rollout:

- primary watcher:
  engineer performing the deploy and smoke checks
- secondary watcher:
  admin/support operator who can verify admin audit UI and student-facing security tab

Observation window:

- active watch:
  first 30 minutes after rollout
- passive watch:
  next business day for newly reported auth/device/audit anomalies

Final sign-off is allowed only after the active watch window is clean and no passive-watch blocker appears.

## 11. Support Debug Notes

If a user reports a problem after rollout:

1. check current mode via `/api/v1/auth/fingerprint-mode`
2. reproduce on `/auth/login`
3. inspect frontend logs for thumbmark/fingerprint errors
4. inspect backend logs for auth/device/audit exceptions
5. inspect latest `student_audit_log` auth rows
6. if the issue is reproducible and touches auth/session/device/audit rendering, switch mode to `off` first, then debug

Default support posture:

- rollback first for auth-path breakage
- investigate after service is stable again
