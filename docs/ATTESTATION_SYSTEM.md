# Система аттестации (автобалансировка)

## Обзор

Система автоматического расчёта баллов студентов на основе:
- Оценок за лабораторные работы (журнал)
- Посещаемости занятий
- Бонусов/штрафов за активность
- **Снапшотов данных при переводе между группами**

**Ключевая особенность:** Преподаватель задаёт веса компонентов и количество работ — система автоматически рассчитывает баллы за каждую работу.

---

## Фиксированные константы (регламент университета)

| Аттестация | Макс баллов | Мин для зачёта | Шкала оценок |
|------------|-------------|----------------|--------------|
| 1-я | 35 | 20 | неуд: 0-19.99, уд: 20-25, хор: 26-30, отл: 31-35 |
| 2-я | 70 | 40 | неуд: 0-39.99, уд: 40-50, хор: 51-60, отл: 61-70 |

---

## Настраиваемые параметры

### Веса компонентов (сумма = 100%)
```
labs_weight: 70%        # Лабораторные работы
attendance_weight: 20%  # Посещаемость
activity_reserve: 10%   # Резерв для бонусов/штрафов
```

### Количество работ
```
labs_count_first: 8     # Лаб для 1-й аттестации
labs_count_second: 10   # Доп. лаб для 2-й аттестации
```

### Коэффициенты оценок
```
grade_5: 1.0  (фикс)    # 100% баллов
grade_4: 0.7  (настр.)  # 70% баллов
grade_3: 0.4  (настр.)  # 40% баллов
grade_2: 0.0  (фикс)    # 0 баллов, требует пересдачи
```

### Посещаемость
```
late_coef: 0.5          # Опоздание = 50% от присутствия
```

---

## Формулы расчёта

### Лабораторные работы
```python
max_labs = attestation_max * (labs_weight / 100)
# Пример: 35 * 0.7 = 24.5 баллов

points_per_work = max_labs / labs_count
# Пример: 24.5 / 8 = 3.06 баллов за 5

work_points = points_per_work * grade_coef
# Пример: 3.06 * 0.7 = 2.14 баллов за 4
```

### Посещаемость
```python
max_attendance = attestation_max * (attendance_weight / 100)
# Пример: 35 * 0.2 = 7 баллов

# EXCUSED не учитывается (занятие как будто не было)
counted_classes = present + late + absent

ratio = (present + late * late_coef) / counted_classes
# Пример: (10 + 2*0.5) / 15 = 0.73

attendance_score = ratio * max_attendance
# Пример: 0.73 * 7 = 5.13 баллов
```

### Активность (с лимитом)
```python
reserve = attestation_max * (activity_reserve / 100)
# Пример: 35 * 0.1 = 3.5 баллов

remaining = attestation_max - current_score
# Если current_score >= max → бонусы заблокированы

max_bonus = min(reserve, remaining)
bonus = min(positive_activity, max_bonus)
penalty = negative_activity  # Без ограничений

activity_score = bonus + penalty
```

### Итоговый балл
```python
total = labs_score + attendance_score + activity_score
final = max(0, min(total, attestation_max))
```

---

## Переводы студентов (StudentTransfer)

При переводе студента между группами создаётся **снапшот** его данных из старой группы:

### Структура снапшота
```python
StudentTransfer:
    attendance_data: {       # Посещаемость из старой группы
        total_lessons: int,
        present: int,
        late: int,
        excused: int,
        absent: int
    }
    lab_grades_data: [       # Оценки за лабы из старой группы
        {work_number: int, grade: int, lesson_id: str}
    ]
    activity_points: float   # Баллы активности на момент перевода
```

### Логика объединения данных
При расчёте аттестации система автоматически:
1. Получает переводы студента в периоде аттестации
2. Объединяет данные из снапшотов с текущими данными новой группы

```python
# Посещаемость
итого_present = текущие.present + sum(снапшоты.present)
итого_late = текущие.late + sum(снапшоты.late)
итого_absent = текущие.absent + sum(снапшоты.absent)

# Лабораторные
все_оценки = текущие_оценки + снапшоты.lab_grades_data

# Активность
итого_активность = текущая + sum(снапшоты.activity_points)
```

### Важно
- Снапшот создаётся **один раз** при переводе и **не обновляется**
- Если данные в старой группе изменятся после перевода — снапшот останется прежним
- Перевод блокируется, если период аттестации уже завершён

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        AttestationService                        │
│                           (facade)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ AttestationSettings │  │ StudentScoreCalc    │               │
│  │      Manager        │  │  (single student)   │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ BatchScoreCalc      │  │ AttestationCalc     │               │
│  │  (group batch)      │  │   (core logic)      │               │
│  └─────────────────────┘  └──────────┬──────────┘               │
│                                      │                           │
│                    ┌─────────────────┼─────────────────┐        │
│                    ▼                 ▼                 ▼        │
│           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│           │LabScoreCalc  │  │AttendanceCalc│  │ActivityCalc  │  │
│           └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Связь с другими модулями

```
┌─────────────────┐
│   LessonGrade   │  Журнал: оценки 2-5 за лабы
│   (Журнал)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Attendance    │  Журнал: PRESENT/LATE/ABSENT/EXCUSED
│  (Посещаемость) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Activity     │  Бонусы/штрафы за активность
│  (Активность)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ StudentTransfer │  Снапшот данных при переводе
│   (Переводы)    │  → объединяется с текущими данными
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│AttestationResult│  Итоговый балл + breakdown
│  (Итог)         │
└─────────────────┘
```

---

## Поток данных

### 1. Журнал → Аттестация

```
POST /journal/grades/bulk
    ↓
crud_lesson_grade.upsert_lesson_grade()
    ↓
LessonGrade (lesson_id, student_id, grade, work_number)
    ↓
StudentScoreCalculator._get_lesson_grades()
    → SELECT LessonGrade JOIN Lesson
    → WHERE student_id = ? AND date BETWEEN period_start/end
    ↓
LabScoreCalculator.calculate(lesson_grades, settings, transfer_grades)
    → points = points_per_work * grade_coef
    → объединяет текущие оценки + снапшоты переводов
```

### 2. Посещаемость → Аттестация

```
POST /journal/attendance/bulk
    ↓
Attendance (student_id, date, status)
    ↓
StudentScoreCalculator._get_attendance()
    → SELECT Attendance WHERE date IN (lesson_dates)
    ↓
AttendanceScoreCalculator.calculate(attendance, settings, transfer_attendance)
    → ratio = (present + late*late_coef) / counted
    → score = ratio * max_attendance
    → объединяет текущую посещаемость + снапшоты переводов
```

### 3. Активность → Аттестация

```
POST /admin/activity
    ↓
Activity (student_id, points, attestation_type)
    ↓
StudentScoreCalculator._get_activity_points()
    → SUM(points) WHERE attestation_type = ?
    ↓
total_activity = db_activity + transfer_activity
    ↓
AttestationCalculator.calculate_activity()
    → bonus с лимитом резерва
    → penalty без ограничений
```

### 4. Перевод студента

```
POST /admin/students/{id}/transfer
    ↓
TransferService.create_transfer()
    ↓
_create_attendance_snapshot()  → attendance_data
_create_lab_grades_snapshot()  → lab_grades_data
_get_activity_points()         → activity_points
    ↓
StudentTransfer (снапшот сохранён)
    ↓
При расчёте аттестации:
StudentScoreCalculator._get_transfers_in_period()
    → SELECT StudentTransfer WHERE attestation_type = ?
    ↓
_merge_transfer_attendance()   → объединение посещаемости
_merge_transfer_lab_grades()   → объединение оценок
_sum_transfer_activity()       → суммирование активности
```

---

## API Endpoints

### Настройки
```
GET  /admin/attestation/settings/{type}     # Получить настройки
PUT  /admin/attestation/settings            # Обновить настройки
GET  /admin/attestation/grade-scale/{type}  # Шкала оценок
```

### Расчёт
```
GET  /admin/attestation/calculate/{student_id}/{type}  # Для студента
GET  /admin/attestation/calculate/group/{group_id}/{type}  # Для группы
```

### Студент
```
GET  /student/attestation/{type}  # Свои баллы
```

### Переводы
```
POST /admin/students/{id}/transfer          # Перевести студента
GET  /admin/students/{id}/transfers         # История переводов
```

---

## Файлы

### Backend
```
backend/app/
├── models/
│   ├── attestation_settings.py    # Модель настроек
│   └── student_transfer.py        # Модель перевода
├── schemas/
│   ├── attestation.py             # Pydantic схемы
│   └── transfer.py                # Схемы переводов
├── services/
│   ├── transfer_service.py        # Сервис переводов
│   └── attestation/
│       ├── __init__.py            # Экспорты
│       ├── service.py             # Facade
│       ├── settings.py            # Менеджер настроек
│       ├── student_score.py       # Расчёт для студента (+переводы)
│       ├── batch.py               # Пакетный расчёт (+переводы)
│       ├── calculator.py          # Основной калькулятор
│       ├── lab_calculator.py      # Расчёт лаб (+transfer_grades)
│       ├── attendance_calculator.py # Расчёт посещаемости (+transfer_attendance)
│       └── constants.py           # Константы
├── api/v1/endpoints/
│   ├── admin_attestation/
│   │   ├── settings.py            # API настроек
│   │   └── calculation.py         # API расчёта
│   ├── admin_stats.py             # API переводов
│   └── student/
│       └── attestation.py         # API студента
└── alembic/versions/
    ├── 036_add_student_transfers.py  # Миграция переводов
    └── 065_autobalance_attestation.py  # Миграция автобалансировки
```

### Frontend
```
frontend/src/
├── lib/api/types/
│   └── attestation.ts             # TypeScript типы
├── components/admin/
│   ├── AttestationSettingsForm.tsx  # Форма настроек
│   └── settings/
│       └── ScorePreviewCard.tsx   # Превью баллов
└── app/admin/attestation/
    └── page.tsx                   # Страница аттестации
```

---

## Пример расчёта (с переводом)

**Настройки:**
- 1-я аттестация (макс 35)
- labs_weight=70%, attendance_weight=20%, activity_reserve=10%
- labs_count_first=8
- grade_4_coef=0.7, grade_3_coef=0.4
- late_coef=0.5

**Данные студента (новая группа):**
- Оценки: 5, 4 (2 лабы)
- Посещаемость: 5 present, 1 late, 1 absent
- Активность: +1 балл

**Снапшот перевода (старая группа):**
- Оценки: 5, 4, 3 (3 лабы)
- Посещаемость: 5 present, 1 late, 2 absent
- Активность: +1 балл

**Расчёт:**

```
1. Лабораторные (текущие + снапшот):
   max_labs = 35 * 0.7 = 24.5
   points_per_work = 24.5 / 8 = 3.0625
   
   Текущие: 5→3.06, 4→2.14
   Снапшот: 5→3.06, 4→2.14, 3→1.23
   
   labs_score = 3.06 + 2.14 + 3.06 + 2.14 + 1.23 = 11.63

2. Посещаемость (текущая + снапшот):
   max_attendance = 35 * 0.2 = 7.0
   
   Объединённые данные:
   present = 5 + 5 = 10
   late = 1 + 1 = 2
   absent = 1 + 2 = 3
   
   ratio = (10 + 2*0.5) / 15 = 0.733
   attendance_score = 0.733 * 7.0 = 5.13

3. Активность (текущая + снапшот):
   total_activity = 1 + 1 = 2
   reserve = 35 * 0.1 = 3.5
   current = 11.63 + 5.13 = 16.76
   remaining = 35 - 16.76 = 18.24
   activity_score = min(2, min(3.5, 18.24)) = 2.0

4. Итого:
   total = 11.63 + 5.13 + 2.0 = 18.76
   grade = "неуд" (< 20)
   is_passing = false
```
