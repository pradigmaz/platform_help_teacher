---
inclusion: always
---

# Правила работы агента

Язык: русский. Стиль: кратко, по делу, с опорой на факты из репозитория.

## Перед началом

1. Сверься с `.kiro/steering/product.md`, `.kiro/steering/structure.md`, `.kiro/steering/tech.md`.
2. Найди существующую реализацию перед созданием новой.
3. Не делай предположений о версиях, командах и путях без проверки в репозитории.

## Основные принципы

- Сначала понять текущий паттерн, потом менять.
- Переиспользование важнее дублирования.
- Малые точечные правки лучше больших абстрактных переписываний.
- Любое утверждение про стек, CI, команды или структуру должно подтверждаться файлами проекта.

## Архитектурные ориентиры

### Backend

```text
Endpoint -> Service -> CRUD -> Model
```

- Endpoint: routing, auth, validation, response shaping
- Service: бизнес-правила, orchestration, интеграция доменов
- CRUD: простые запросы и data access helpers
- Model/Schema: структура хранения и контракт

### Frontend

```text
Page -> Component -> Hook/Lib -> API
```

- App Router по умолчанию
- client components только где нужен browser state/events
- `lib/api/` и `schema.d.ts` — источник типизированного API-контракта

## Что проверять перед изменениями

- Есть ли уже похожий endpoint/service/component/test
- Есть ли существующий тест, который должен защитить изменение
- Нужно ли обновить `.kiro/steering/*` или другие docs после изменения поведения
- Затрагивает ли задача миграции, rollout, backup, audit или security paths

## Проверка после изменений

Выбирай только релевантные проверки, но не пропускай явные gates.

### Backend

```bash
cd backend
./venv/bin/ruff check app
./venv/bin/ruff format --check app
./venv/bin/pytest -v --tb=short
```

### Frontend

```bash
cd frontend
npx tsc --noEmit
npm run lint
npm run build
```

### Расширенные тесты

Используй отдельный tool env, а не `backend/venv`:

```bash
cd /home/zaikana/Рабочий стол/platforma_maga
.venvs/testing-stack/bin/schemathesis --help
.venvs/testing-stack/bin/mutmut --help
.venvs/testing-stack/bin/python -m pytest
```

## Ограничения и аккуратность

- Не смешивай runtime env backend с тяжёлыми experimental test tools без причины.
- Не редактируй старые миграции ради косметики.
- Не трогай боевые данные без backup/recovery path.
- Для cleanup/data-repair scripts сначала обеспечь безопасный откат.
- Не меняй shared UI primitives без понимания системного эффекта.

## Где искать в первую очередь

### Backend

- `backend/app/api/v1/endpoints/`
- `backend/app/services/`
- `backend/app/crud/`
- `backend/app/audit/`
- `backend/tests/`
- `backend/scripts/`

### Frontend

- `frontend/src/app/`
- `frontend/src/components/`
- `frontend/src/hooks/`
- `frontend/src/lib/api/`
- `frontend/src/lib/fingerprint/`
- colocated `*.test.ts[x]`

## Для сложных задач

- Разбей задачу на шаги и зафиксируй план в `.kiro/todo-[task].md`
- После завершения — краткий отчёт в `.kiro/report-[task].md`
- Если меняется поведение системы, синхронизируй steering-доки и релевантные рабочие docs

## Документация

- `.kiro/steering/product.md` — продукт и домены
- `.kiro/steering/structure.md` — структура репозитория
- `.kiro/steering/tech.md` — версии, команды, CI и тестовый стек

Если эти файлы расходятся с реальным кодом, сначала исправь документацию, затем опирайся на неё.
