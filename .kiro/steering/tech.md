---
inclusion: always
---

# Tech Stack

## Backend

- Python `3.11+`
- FastAPI `0.135.1`
- Pydantic `2.x`
- SQLAlchemy `2.0.36` + Alembic `1.14.0`
- PostgreSQL `16`
- Redis `7.2.x`
- Celery `5.4.0`
- MinIO
- aiogram `3.26.0`
- Playwright Python dependency присутствует в backend requirements

## Frontend

- Next.js `16.0.10`
- React `19.2.1`
- TypeScript `5.x`
- Tailwind CSS `4`
- Radix UI
- Zustand
- React Hook Form + Zod
- Lexical editor
- Browser testing: `@playwright/test`
- Component/unit testing: `Vitest`, `Testing Library`, `fast-check`

## Infra и runtime

- Локальная разработка: `deploy/docker-compose.dev.yml`
- Сервисы dev-compose: `db`, `redis`, `minio`, `backend`, `frontend`, `celery-worker`, `celery-beat`, `nginx`
- Продовый деплой: GitHub Actions CD на self-hosted VPS runner
- В CI используется:
  - Node `20`
  - Python `3.11`

## Тестовый стек

### Обычные project checks

- Backend:
  - `ruff check app`
  - `ruff format --check app`
  - `pytest -v --tb=short`
- Frontend:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `npm run build`

### Расширенный тестовый стек

Для исследовательских и тяжёлых тестов используется отдельное локальное окружение:

- `.venvs/testing-stack`

В нём живут:

- `schemathesis`
- `mutmut`
- `testcontainers`
- `pytest-playwright`
- отдельный `playwright`

Это сделано специально, чтобы не ломать pinned backend runtime dependencies.

## CI на сегодня

GitHub Actions проверяет:

- Frontend: install -> typecheck -> eslint -> build
- Backend Lint: install -> `ruff check` -> `ruff format --check`
- Backend Tests: install -> create test `.env` -> `pytest -v --tb=short`
- Security:
  - `pip-audit` по `backend/requirements.txt`
  - `npm audit --audit-level=high`
- Migration Check:
  - проверка дубликатов migration prefixes

`mypy` запускается, но сейчас не является блокирующим gate: `mypy app || true`.

## Команды

### Локальный dev-стек

```bash
docker compose -f deploy/docker-compose.dev.yml --env-file deploy/.env.dev up -d --build
```

### Backend

```bash
cd backend
./venv/bin/pytest -v --tb=short
./venv/bin/ruff check app
./venv/bin/ruff format --check app
```

### Frontend

```bash
cd frontend
npx tsc --noEmit
npm run lint
npm run build
npm run generate-types
```

### Расширенные тестовые инструменты

```bash
cd /home/zaikana/Рабочий стол/platforma_maga
.venvs/testing-stack/bin/schemathesis --help
.venvs/testing-stack/bin/mutmut --help
.venvs/testing-stack/bin/python -m pytest
docker run --rm -i grafana/k6 run - < script.js
```

## Правила по коду

### Python

- async-first для endpoint/service/DB paths
- type hints обязательны
- ошибки через `HTTPException` или доменные исключения
- `logging`, не `print`
- бизнес-логика не должна уезжать в endpoint

### TypeScript

- App Router по умолчанию
- без `any` там, где можно выразить тип
- формы через RHF + Zod
- API-типизация от `frontend/src/lib/api/schema.d.ts`

### SQL / миграции

- `snake_case`
- индексы с внятным именованием
- только forward migrations
- старые миграции не переписывать без реальной необходимости

## Практические замечания

- `backend/venv` оставляем чистым для runtime и обычных тестов.
- Тяжёлые тестовые зависимости не надо ставить туда напрямую, если они конфликтуют с pinned стеком.
- `.kiro/steering/` — локальная документация и контекст для разработки; в продовый deploy artifact она не попадает.
