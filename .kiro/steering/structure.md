---
inclusion: always
---

# Структура проекта

## Репозиторий

```text
backend/          FastAPI, модели, миграции, тесты, scripts
frontend/         Next.js App Router, UI, hooks, API client, browser tests
deploy/           docker compose, env templates, nginx, VPS scripts
backups/          локальные dump/restore артефакты
.kiro/steering/   product/structure/tech/agent rules для Kiro
md/               исследовательские заметки и audit-отчёты
.venvs/           локальные служебные окружения, включая testing-stack
```

## Backend

### Основные каталоги

```text
backend/app/
  api/v1/endpoints/   HTTP-слой, разрезанный по доменам и подпакетам
  audit/              audit pipeline, schemas, storage, suspicion scoring
  core/               config, security, csrf, limiter, redis, logging
  crud/               простые DB-операции; есть подпакеты `attendance/`, `report/`
  db/                 session / engine setup
  middleware/         IP ban, security monitor hooks
  models/             SQLAlchemy модели
  schemas/            Pydantic response/input схемы
  services/           бизнес-логика и orchestration
  tasks/              Celery tasks
  bots/               Telegram/VK bots
  utils/              чистые утилиты
```

### Реальные backend-паттерны

- `api/v1/endpoints/` уже не плоский: есть подпакеты `admin_attestation/`, `admin_labs/`, `backup/`, `groups/`, `journal/`, `student/`.
- `services/` смешивает зрелые пакеты и legacy flat-файлы.
- Для крупных областей уже есть отдельные пакеты:
  - `services/attestation/`
  - `services/backup/`
  - `services/bot/`
  - `services/export/`
  - `services/lab_visibility/`
  - `services/rate_limit/`
  - `services/reports/`
  - `services/security_monitor/`
- В новых изменениях лучше продолжать пакетный подход для растущих доменов, а не плодить новые monolithic `*_service.py`.

### Backend tests и scripts

```text
backend/tests/       pytest suite, включая auth, labs, attestation, audit, sessions
backend/scripts/     одноразовые/операционные скрипты
backend/alembic/     миграции
```

- На момент обновления steering backend собирает `491` тест через `pytest --collect-only`.
- Для операций с данными уже есть отдельные safe scripts, например `cleanup_audit_noise.py`.

## Frontend

### Основные каталоги

```text
frontend/src/
  app/               App Router pages/layouts
  components/        доменные компоненты, shared UI, editor blocks
  hooks/             React hooks
  lib/               API client, fingerprint, shared helpers/constants
  types/             общие типы
```

### Реальная структура frontend

- `app/admin/*` содержит основные admin flows: audit, journal, labs, schedule, groups, settings, students.
- `app/dashboard/*` содержит student cabinet.
- Есть отдельные public/student-facing маршруты: `labs/view`, `lectures/view`, `report/[code]`.
- В `components/` живут:
  - `ui/` — shared primitives и design-system слой
  - `admin/`, `dashboard/`, `labs/`, `lectures/`, `schedule/`, `feedback/`, `notes/`
  - `animate-ui/` и `molecule-ui/` — composable UI blocks
- В `lib/api/` лежит typed API слой и сгенерированный `schema.d.ts`.
- В `lib/fingerprint/` живёт frontend fingerprint/mode логика.
- Тесты уже colocated рядом с кодом: `*.test.ts` / `*.test.tsx`.

## Куда класть новое

| Что                          | Куда                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| Новый admin endpoint         | `backend/app/api/v1/endpoints/admin_{domain}.py` или подпакет `admin_{domain}/` |
| Новый student endpoint       | `backend/app/api/v1/endpoints/student/{feature}.py`                             |
| Новый backend domain package | `backend/app/services/{domain}/` если область уже больше одного файла           |
| Простая DB-операция          | `backend/app/crud/...`                                                          |
| Операционный script          | `backend/scripts/{task}.py`                                                     |
| Новая admin page             | `frontend/src/app/admin/{route}/page.tsx`                                       |
| Новая student page           | `frontend/src/app/dashboard/{route}/page.tsx`                                   |
| API helper                   | `frontend/src/lib/api/{domain}.ts`                                              |
| Fingerprint/session UI logic | `frontend/src/lib/fingerprint/` или `frontend/src/components/dashboard/`        |
| Browser/component test       | рядом с кодом через `*.test.ts[x]`                                              |

## Переиспользование

Перед созданием нового кода сначала ищи:

- backend services и existing endpoint packages;
- `frontend/src/components/ui/` и `components/*` по доменам;
- `frontend/src/lib/api/` и `schema.d.ts`;
- `backend/tests/` и colocated frontend tests для готовых паттернов.

## Локальные окружения

- Обычная backend-разработка и pytest: `backend/venv`
- Расширенный тестовый стек (`schemathesis`, `mutmut`, `testcontainers`, отдельный `playwright`): `.venvs/testing-stack`

Не смешивай repo tool venv с runtime-окружением backend без явной необходимости.
