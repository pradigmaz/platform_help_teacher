---
inclusion: always
---

# Edu Platform

Веб-платформа для учебного процесса: журнал, лабы, аттестация, расписание, контент, аудит и безопасность.

## Роли

- **ADMIN**: системные настройки, аудит, безопасность, бэкапы, impersonation
- **TEACHER**: свои группы, журнал, лабы, материалы, отчёты
- **STUDENT**: личный кабинет, просмотр расписания и материалов, сдача работ

Ownership и видимость завязаны на `backend/app/api/ownership.py`, группах, предметах и статусе пользователя.

## Ключевые продуктовые зоны

| Зона                 | Что делает                                                             |
| -------------------- | ---------------------------------------------------------------------- |
| Группы и студенты    | состав групп, подгруппы, переводы, инвайт-коды                         |
| Журнал               | занятия, посещаемость, оценки, массовые операции, экспорт              |
| Лабы                 | публикация, дедлайны, extensions, очередь на защиту, submissions       |
| Аттестация           | расчёт итоговых баллов по весам и правилам группы/предмета             |
| Расписание           | импорт, парсинг, отображение, привязка лаб и занятий                   |
| Контент              | лекции, заметки, объявления, медиа                                     |
| Аудит и безопасность | audit log, security monitor, rate limit, IP ban, подозрительные сессии |
| Сессии и устройства  | device binding, fingerprint mode, пользовательские сессии              |
| Отчёты и экспорт     | публичные и внутренние отчёты, CSV/XLSX                                |
| Бэкапы               | создание, хранение, восстановление, remote storage                     |

## Основные сущности

| Домен           | Ключевые таблицы / модели                                                          |
| --------------- | ---------------------------------------------------------------------------------- |
| Пользователи    | `users`, `user_groups`, `devices`, `user_sessions`, `notification_settings`        |
| Учебный процесс | `groups`, `subjects`, `lessons`, `attendance`, `lesson_grade`, `student_transfers` |
| Лабы            | `labs`, `lab_settings`, `work_submission`, `lab_deadline_extension`                |
| Аттестация      | `attestation_settings`, `activity`                                                 |
| Контент         | `lectures`, `lecture_images`, `notes`, `announcements`                             |
| Расписание      | `schedules`, `schedule_parser_config`, `parse_history`                             |
| Аудит           | `student_audit_log*`, `suspicion_ban*`, security-related read models               |
| Отчёты          | `group_reports`, `report_views`                                                    |
| Бэкапы          | `backup_settings` и MinIO buckets                                                  |

## Бизнес-правила

### Аттестация

```text
score = labs*w1 + attendance*w2 + activity*w3 + manual*w4
```

- Веса настраиваются глобально и по предмету/группе.
- При отключении компонента используется autobalance.
- Есть отдельные проверки дедлайнов, lab slots и subject scope.

### Лабы

- Базовый поток: `draft -> published -> archived`
- Дедлайны могут идти от занятия, расписания и ручных extensions.
- Студенческая выдача зависит от видимости, дедлайнов и состояния submission.
- Очередь на защиту и acceptance-context влияют на доступные действия.

### Журнал

- Посещаемость: `present`, `absent`, `late`, `excused`
- Оценки: `0-100`
- Операции и отчёты учитывают группы, подгруппы и связь с лабораторными сдачами.

### Сессии и безопасность

- JWT + refresh/session flow
- Device binding и fingerprint mode используются для проверки сессий и админских сценариев
- CSRF, rate limiting, IP ban, honeypot, audit и security monitor входят в базовую защиту

## API-карта

| Префикс             | Доступ               | Назначение                                                            |
| ------------------- | -------------------- | --------------------------------------------------------------------- |
| `/api/v1/auth/*`    | public/authenticated | логин, refresh, fingerprint/dev-login, session flow                   |
| `/api/v1/admin/*`   | ADMIN                | аудит, безопасность, отчёты, настройки, impersonation, schedule, labs |
| `/api/v1/groups/*`  | TEACHER+             | группы, студенты, подгруппы, настройки                                |
| `/api/v1/journal/*` | TEACHER+             | занятия, посещаемость, оценки, экспорт                                |
| `/api/v1/labs/*`    | TEACHER+/STUDENT     | лабораторные и student-facing lab views                               |
| `/api/v1/student/*` | STUDENT              | личный кабинет, прогресс, attendance, labs, profile                   |
| `/api/v1/backup/*`  | ADMIN                | backup settings, restore, cleanup                                     |
| `/api/v1/public_*`  | public               | публичные отчёты и служебные public views                             |

## Интеграции

- **Telegram Bot**: webhook, auth/notifications, user binding
- **VK Bot**: long polling и social identity binding
- **MinIO**: вложения, изображения, backup storage
- **Redis**: rate limit, Celery broker/result backend, security/session вспомогательные потоки

## Ключевые пути в коде

| Что                  | Где                                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Аттестация           | `backend/app/services/attestation/`                                                                                  |
| Журнал               | `backend/app/api/v1/endpoints/journal/`, `backend/app/services/journal_*`                                            |
| Лабы                 | `backend/app/api/v1/endpoints/admin_labs/`, `backend/app/services/lab_*`, `backend/app/services/submission_*`        |
| Аудит                | `backend/app/audit/`, `frontend/src/app/admin/audit/`                                                                |
| Сессии и fingerprint | `backend/app/services/session_service.py`, `backend/app/services/device_service.py`, `frontend/src/lib/fingerprint/` |
| Бэкапы               | `backend/app/api/v1/endpoints/backup/`, `backend/app/services/backup/`                                               |
| Безопасность         | `backend/app/middleware/`, `backend/app/services/security_monitor/`, `backend/app/services/rate_limit/`              |
