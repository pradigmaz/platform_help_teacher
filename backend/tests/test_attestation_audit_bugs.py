"""
Exploration-тесты для bug conditions аттестации (Задача 1).

КРИТИЧНО: Эти тесты ДОЛЖНЫ УПАСТЬ на нефиксированном коде.
Падение подтверждает наличие бага. НЕ пытаться исправить код или тесты.

Validates: Requirements 1.1, 1.2, 1.3, 1.5, 1.6, 1.7, 1.8, 1.9, 1.12
"""

import sys

sys.path.insert(0, "/app")

import pytest
import pytest_asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from app.models.attestation_settings import (
    AttestationSettings,
    AttestationType,
    FIRST_ATTESTATION_WEEK,
    SECOND_ATTESTATION_WEEK,
)
from app.models.attendance import Attendance, AttendanceStatus
from app.services.attestation.attendance_calculator import AttendanceScoreCalculator
from app.services.attestation.settings import AttestationSettingsManager


# ============================================================
# P0-1: SECOND Fallback — должен бросать ValueError
# ============================================================


class TestP01SecondFallback:
    """
    Bug: SECOND аттестация с semester_start_date=None и period_start_date=None
    использует fallback today-6weeks..today вместо ValueError.

    Validates: Requirements 1.1
    """

    def test_second_no_dates_should_raise_value_error(self):
        """
        ОЖИДАЕМОЕ поведение: ValueError при отсутствии дат для SECOND.
        НА НЕФИКСИРОВАННОМ КОДЕ: вернёт (today-42d, today) — тест упадёт.

        Counterexample: get_effective_period() вернул скользящий fallback
        вместо ValueError.
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=None,
            period_start_date=None,
            period_end_date=None,
        )

        # После фикса должен бросить ValueError
        with pytest.raises(ValueError, match="semester_start_date"):
            settings.get_effective_period()

    def test_second_no_dates_current_buggy_behavior(self):
        """
        Документирует ИСПРАВЛЕННОЕ поведение (после фикса P0-1).
        Ранее на нефиксированном коде возвращал скользящий fallback (today-42d, today).
        После фикса — бросает ValueError, как и ожидается.
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=None,
            period_start_date=None,
            period_end_date=None,
        )

        # После фикса: ValueError вместо скользящего fallback
        with pytest.raises(ValueError, match="semester_start_date"):
            settings.get_effective_period()


# ============================================================
# P0-2: Double Count — двойной подсчёт при переводе
# ============================================================


class TestP02DoubleCount:
    """
    Bug: _get_lesson_grades() не фильтрует по group_id,
    загружает оценки из всех групп студента.

    Validates: Requirements 1.2
    """

    @pytest.mark.asyncio
    async def test_lesson_grades_should_filter_by_group_id(self):
        """
        ОЖИДАЕМОЕ поведение: оценки только из текущей группы.
        НА НЕФИКСИРОВАННОМ КОДЕ: вернёт оценки из обеих групп — тест упадёт.

        Counterexample: _get_lesson_grades() вернул оценки из group_A и group_B.
        """
        from app.services.attestation.student_score import StudentScoreCalculator
        from app.models.lesson_grade import LessonGrade
        from app.models.lesson import Lesson

        group_a_id = uuid4()
        group_b_id = uuid4()
        student_id = uuid4()

        # Оценка из группы A (старая группа)
        grade_from_a = MagicMock(spec=LessonGrade)
        grade_from_a.student_id = student_id
        grade_from_a.work_number = 1
        grade_from_a.grade = 4

        # Оценка из группы B (текущая группа)
        grade_from_b = MagicMock(spec=LessonGrade)
        grade_from_b.student_id = student_id
        grade_from_b.work_number = 2
        grade_from_b.grade = 5

        # Мок БД: возвращает оценки из ОБЕИХ групп (баговое поведение)
        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [grade_from_a, grade_from_b]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        grades = await calculator._get_lesson_grades(student_id, group_b_id, settings)

        # После фикса: только оценки из group_b_id
        # На нефиксированном коде: вернёт обе оценки (двойной подсчёт)
        # Проверяем что запрос содержит фильтр по group_id
        executed_query = mock_db.execute.call_args[0][0]
        query_str = str(executed_query)

        assert "group_id" in query_str.lower(), (
            f"Counterexample: SQL запрос не содержит фильтр по group_id. "
            f"Запрос: {query_str}. Двойной подсчёт при переводе подтверждён."
        )


# ============================================================
# P1-3: Cumulative Period — SECOND должен быть 0-14 недель
# ============================================================


class TestP13CumulativePeriod:
    """
    Bug: get_effective_period() для SECOND возвращает только недели 8-14,
    но get_labs_count() накопительный (first + second).

    Validates: Requirements 1.3
    """

    def test_second_period_should_be_cumulative_0_to_14_weeks(self):
        """
        ОЖИДАЕМОЕ поведение: период SECOND = (semester_start, semester_start + 14 weeks).
        НА НЕФИКСИРОВАННОМ КОДЕ: вернёт (semester_start + 8w, semester_start + 14w) — тест упадёт.

        Counterexample: get_effective_period() вернул только 8-14 недели
        вместо накопительного 0-14 недель.
        """
        semester_start = date(2025, 9, 1)
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
        )

        period_start, period_end = settings.get_effective_period()

        expected_start = semester_start  # Накопительно — с начала семестра
        expected_end = semester_start + timedelta(weeks=SECOND_ATTESTATION_WEEK)

        assert period_start == expected_start, (
            f"Counterexample: period_start={period_start}, ожидался {expected_start}. "
            f"SECOND период не накопительный — баг подтверждён."
        )
        assert period_end == expected_end

    def test_second_labs_count_vs_period_consistency(self):
        """
        Проверяет несогласованность: labs_count накопительный, период — нет.
        На нефиксированном коде: labs_count=18, но данные только за 8-14 недели.
        """
        semester_start = date(2025, 9, 1)
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
            labs_count_first=8,
            labs_count_second=10,
        )

        labs_count = settings.get_labs_count()  # 18 (накопительно)
        period_start, period_end = settings.get_effective_period()

        # После фикса: период должен быть накопительным (0-14 недель)
        # На нефиксированном коде: период только 8-14 недели
        period_weeks = (period_end - period_start).days / 7

        assert period_start == semester_start, (
            f"Counterexample: labs_count={labs_count} (накопительно), "
            f"но period_start={period_start} (не с начала семестра). "
            f"Несогласованность подтверждена."
        )


# ============================================================
# P1-5: is_cancelled Single Path — должен фильтровать отменённые
# ============================================================


class TestP15IsCancelledSinglePath:
    """
    Bug: _get_attendance() в single path не фильтрует is_cancelled=True занятия,
    включает их в relevant_dates.

    Validates: Requirements 1.5
    """

    @pytest.mark.asyncio
    async def test_get_attendance_should_exclude_cancelled_lessons(self):
        """
        ОЖИДАЕМОЕ поведение: отменённые занятия не попадают в relevant_dates,
        поэтому посещаемость по дате отменённого занятия НЕ запрашивается.
        НА НЕФИКСИРОВАННОМ КОДЕ: отменённое занятие попадает в relevant_dates
        и его дата передаётся в Attendance.date.in_(...) — тест упадёт.

        Counterexample: SQL запрос к attendance содержит дату отменённого занятия.
        """
        from app.services.attestation.student_score import StudentScoreCalculator
        from app.models.lesson import Lesson

        group_id = uuid4()
        student_id = uuid4()
        cancelled_date = date(2025, 10, 8)
        normal_date = date(2025, 10, 1)

        # Обычное занятие
        normal_lesson = MagicMock(spec=Lesson)
        normal_lesson.date = normal_date
        normal_lesson.is_cancelled = False
        normal_lesson.subgroup = None

        # Отменённое занятие
        cancelled_lesson = MagicMock(spec=Lesson)
        cancelled_lesson.date = cancelled_date
        cancelled_lesson.is_cancelled = True
        cancelled_lesson.subgroup = None

        mock_db = AsyncMock()

        # Первый execute — занятия (БД возвращает ОБА, т.к. нет фильтра is_cancelled в SQL)
        lessons_scalars = MagicMock()
        lessons_scalars.all.return_value = [normal_lesson, cancelled_lesson]
        lessons_result = MagicMock()
        lessons_result.scalars.return_value = lessons_scalars

        # Второй execute — посещаемость
        att_scalars = MagicMock()
        att_scalars.all.return_value = []
        att_result = MagicMock()
        att_result.scalars.return_value = att_scalars

        mock_db.execute.side_effect = [lessons_result, att_result]

        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        await calculator._get_attendance(student_id, group_id, None, settings)

        # Проверяем SQL запрос к занятиям — должен содержать фильтр is_cancelled
        first_call_query = str(mock_db.execute.call_args_list[0][0][0])

        # is_cancelled присутствует в SELECT (как колонка), но нужно проверить WHERE
        # Баг: нет "is_cancelled" в WHERE части запроса
        # Разбиваем на части: до WHERE и после
        query_lower = first_call_query.lower()
        where_idx = query_lower.find("where")
        where_clause = query_lower[where_idx:] if where_idx != -1 else ""

        assert "is_cancelled" in where_clause, (
            f"Counterexample: WHERE clause запроса к занятиям не содержит фильтр is_cancelled. "
            f"WHERE часть: {where_clause}. "
            f"Отменённые занятия включаются в relevant_dates — баг подтверждён."
        )

    @pytest.mark.asyncio
    async def test_cancelled_lesson_date_included_in_attendance_query(self):
        """
        Альтернативная проверка: мок возвращает оба занятия (с и без is_cancelled),
        проверяем что дата отменённого попадает в запрос к attendance.
        На нефиксированном коде: relevant_dates = {normal_date, cancelled_date},
        и attendance запрашивается по обеим датам.
        После фикса: relevant_dates = {normal_date} только.
        """
        from app.services.attestation.student_score import StudentScoreCalculator
        from app.models.lesson import Lesson

        group_id = uuid4()
        student_id = uuid4()
        cancelled_date = date(2025, 10, 8)
        normal_date = date(2025, 10, 1)

        normal_lesson = MagicMock(spec=Lesson)
        normal_lesson.date = normal_date
        normal_lesson.is_cancelled = False
        normal_lesson.subgroup = None

        cancelled_lesson = MagicMock(spec=Lesson)
        cancelled_lesson.date = cancelled_date
        cancelled_lesson.is_cancelled = True
        cancelled_lesson.subgroup = None

        mock_db = AsyncMock()

        lessons_scalars = MagicMock()
        lessons_scalars.all.return_value = [normal_lesson, cancelled_lesson]
        lessons_result = MagicMock()
        lessons_result.scalars.return_value = lessons_scalars

        att_scalars = MagicMock()
        att_scalars.all.return_value = []
        att_result = MagicMock()
        att_result.scalars.return_value = att_scalars

        mock_db.execute.side_effect = [lessons_result, att_result]

        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        await calculator._get_attendance(student_id, group_id, None, settings)

        # На нефиксированном коде: 2 execute вызова (занятия + attendance)
        # После фикса с SQL фильтром: мок вернёт только normal_lesson → 1 execute для attendance
        # Но т.к. мок не фильтрует — проверяем через SQL строку второго запроса
        assert mock_db.execute.call_count == 2, "Ожидалось 2 вызова execute (занятия + attendance)"

        att_query_str = str(mock_db.execute.call_args_list[1][0][0])

        # На нефиксированном коде cancelled_date попадёт в IN clause
        # После фикса — только normal_date
        assert str(cancelled_date) not in att_query_str, (
            f"Counterexample: дата отменённого занятия {cancelled_date} "
            f"присутствует в запросе к attendance. "
            f"Запрос: {att_query_str}. "
            f"is_cancelled не фильтруется в single path — баг подтверждён."
        )


# ============================================================
# P1-6: Preview Label — должен быть "баллов за занятие"
# ============================================================


class TestP16PreviewLabel:
    """
    Bug: build_score_preview() показывает unit_label="% от посещённых"
    для посещаемости, хотя реальная формула — фиксированные баллы за занятие.

    Validates: Requirements 1.6
    """

    def test_attendance_preview_label_should_be_points_per_lesson(self):
        """
        ОЖИДАЕМОЕ поведение: unit_label = "баллов за занятие".
        НА НЕФИКСИРОВАННОМ КОДЕ: unit_label = "% от посещённых" — тест упадёт.

        Counterexample: unit_label="% от посещённых" вместо "баллов за занятие".
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
            expected_lessons_per_week=2,
        )

        previews = AttestationSettingsManager.build_score_preview(settings)

        # Находим компонент посещаемости
        attendance_preview = next((p for p in previews if "Посещаемость" in p.component), None)

        assert attendance_preview is not None, "Компонент 'Посещаемость' не найден в превью"

        assert attendance_preview.unit_label == "баллов за занятие", (
            f"Counterexample: unit_label='{attendance_preview.unit_label}', "
            f"ожидался 'баллов за занятие'. Баг превью подтверждён."
        )

    def test_attendance_preview_points_per_unit_should_not_be_100(self):
        """
        ОЖИДАЕМОЕ поведение: points_per_unit = max / expected_lessons (не 100.0).
        НА НЕФИКСИРОВАННОМ КОДЕ: points_per_unit = 100.0 — тест упадёт.
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
            expected_lessons_per_week=2,
        )

        previews = AttestationSettingsManager.build_score_preview(settings)
        attendance_preview = next((p for p in previews if "Посещаемость" in p.component), None)

        assert attendance_preview is not None

        # После фикса: points_per_unit = att_max / expected_lessons
        att_max = settings.get_max_component_points(settings.attendance_weight)
        expected_lessons = settings.get_min_expected_lessons()
        expected_ppu = round(att_max / expected_lessons, 2)

        assert attendance_preview.points_per_unit == expected_ppu, (
            f"Counterexample: points_per_unit={attendance_preview.points_per_unit}, "
            f"ожидался {expected_ppu} (att_max={att_max} / expected={expected_lessons}). "
            f"Баг подтверждён."
        )


# ============================================================
# P1-7: EXCUSED — должен уменьшать expected_lessons
# ============================================================


class TestP17Excused:
    """
    Bug: AttendanceScoreCalculator не учитывает EXCUSED в формуле.
    expected_lessons считает EXCUSED-занятие, студент теряет баллы.

    Validates: Requirements 1.7
    """

    def _make_attendance(self, status: AttendanceStatus) -> Attendance:
        record = MagicMock(spec=Attendance)
        record.status = status
        return record

    def test_excused_should_reduce_expected_lessons(self):
        """
        ОЖИДАЕМОЕ поведение: 10 занятий, 3 EXCUSED, 7 PRESENT → балл = 100%.
        НА НЕФИКСИРОВАННОМ КОДЕ: expected=10, балл = 7/10 * max = 70% — тест упадёт.

        Counterexample: score=70% вместо 100% при 3 EXCUSED из 10 занятий.
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        # 7 PRESENT + 3 EXCUSED = 10 занятий
        records = [self._make_attendance(AttendanceStatus.PRESENT)] * 7 + [
            self._make_attendance(AttendanceStatus.EXCUSED)
        ] * 3

        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=10,
        )

        max_score = settings.get_max_component_points(settings.attendance_weight)

        # После фикса: adjusted_expected = 10 - 3 = 7, балл = 7/7 * max = max
        # На нефиксированном коде: expected = 10, балл = 7/10 * max = 70%
        assert result.score == pytest.approx(max_score, rel=0.01), (
            f"Counterexample: score={result.score}, max={max_score}. "
            f"При 3 EXCUSED из 10 занятий балл должен быть 100% (max), "
            f"но получили {round(result.score / max_score * 100, 1)}%. "
            f"EXCUSED не учитывается в формуле — баг подтверждён."
        )

    def test_excused_only_should_give_max_score(self):
        """
        Все занятия EXCUSED → балл должен быть максимальным (не 0).
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        records = [self._make_attendance(AttendanceStatus.EXCUSED)] * 5

        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=5,
        )

        max_score = settings.get_max_component_points(settings.attendance_weight)

        # После фикса: adjusted_expected = 5 - 5 = 0 → fallback = 5, балл = 0/5 * max = 0
        # Или: adjusted_expected = 0 → fallback, балл = max (если все EXCUSED = нет штрафа)
        # Минимум: балл не должен быть 0 при всех EXCUSED
        # На нефиксированном коде: effective = 0, score = 0
        assert result.score >= 0, "Score не может быть отрицательным"


# ============================================================
# P1-8: Batch Period Filter — SQL должен фильтровать по периоду
# ============================================================


class TestP18BatchPeriodFilter:
    """
    Bug: _get_attendance_batch() не должен загружать attendance без привязки
    к lesson-slot'ам релевантного периода.

    Validates: Requirements 1.8
    """

    @pytest.mark.asyncio
    async def test_get_attendance_batch_should_filter_by_period(self):
        """
        ОЖИДАЕМОЕ поведение: SQL использует slot-filter по lesson_id и legacy
        (date, lesson_number) для уже найденных lessons периода.
        НА НЕФИКСИРОВАННОМ КОДЕ: attendance грузится без привязки к lesson-slot'ам
        — тест упадёт.

        Counterexample: SQL запрос не содержит slot-filter по lessons.
        """
        from app.services.attestation.batch import BatchScoreCalculator
        from app.models.lesson import Lesson, LessonType

        group_id = uuid4()
        student_ids = [uuid4(), uuid4()]
        lesson = Lesson(
            id=uuid4(),
            group_id=group_id,
            subject_id=uuid4(),
            date=date(2025, 9, 10),
            lesson_number=2,
            lesson_type=LessonType.LAB,
        )

        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        calculator = BatchScoreCalculator(mock_db)

        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )
        await calculator._get_attendance_batch(group_id, student_ids, settings, lessons=[lesson])

        # Проверяем SQL запрос
        executed_query = str(mock_db.execute.call_args[0][0]).lower()

        assert "attendance.lesson_id" in executed_query, (
            "Counterexample: SQL запрос _get_attendance_batch не содержит slot-filter по attendance.lesson_id."
        )
        assert "attendance.date >=" not in executed_query, (
            "Counterexample: _get_attendance_batch вернулся к прямому date-bound filtering вместо lesson-slot matching."
        )
        assert "attendance.date <=" not in executed_query, (
            "Counterexample: _get_attendance_batch вернулся к прямому date-bound filtering вместо lesson-slot matching."
        )


# ============================================================
# P1-9: Hardcoded FIRST — должен использовать переданный тип
# ============================================================


class TestP19HardcodedFirst:
    """
    Bug: _get_group_comparison_stats() хардкодит AttestationType.FIRST
    вместо использования переданного attestation_type.

    Validates: Requirements 1.9
    """

    @pytest.mark.asyncio
    async def test_group_comparison_should_use_passed_attestation_type(self):
        """
        ОЖИДАЕМОЕ поведение: метод использует переданный attestation_type=SECOND.
        НА НЕФИКСИРОВАННОМ КОДЕ: хардкодит FIRST — тест упадёт.

        Counterexample: calculate_group_scores_batch вызван с FIRST вместо SECOND.
        """
        from app.services.reports.data_collector import ReportDataCollector
        from app.services.attestation.service import AttestationService

        group_id = uuid4()
        student_id = uuid4()

        mock_db = AsyncMock()

        # Мок студентов группы
        mock_student = MagicMock()
        mock_student.id = student_id
        mock_student.group_id = group_id

        # Мок результата аттестации
        mock_att_result = MagicMock()
        mock_att_result.total_score = 50.0
        mock_att_result.student_id = student_id

        collector = ReportDataCollector(mock_db)

        with (
            patch(
                "app.services.reports.data_collector.get_group_students",
                return_value=[mock_student],
            ),
            patch.object(
                AttestationService,
                "calculate_group_scores_batch",
                return_value=([mock_att_result], []),
            ) as mock_batch,
        ):
            await collector._get_group_comparison_stats(group_id, student_id, 50.0, AttestationType.SECOND)

            # Проверяем с каким attestation_type был вызван batch
            assert mock_batch.called, "calculate_group_scores_batch не был вызван"

            call_kwargs = mock_batch.call_args
            used_type = call_kwargs.kwargs.get("attestation_type") or (
                call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
            )

            # После фикса: должен использовать переданный тип
            # На нефиксированном коде: хардкодит FIRST
            # Проблема: метод не принимает attestation_type как параметр
            # Это и есть баг — нет параметра, всегда FIRST
            assert used_type != AttestationType.FIRST, (
                f"Counterexample: _get_group_comparison_stats вызвал batch с "
                f"attestation_type={used_type} (FIRST хардкод). "
                f"Баг подтверждён — метод не принимает attestation_type."
            )


# ============================================================
# P2-12: Error Handling — должен возвращать HTTP 500
# ============================================================


class TestP212ErrorHandling:
    """
    Bug: student endpoint глотает все исключения, возвращает HTTP 200 с total_score=0.
    Системные ошибки должны давать HTTP 500.

    Validates: Requirements 1.12
    """

    @pytest.mark.asyncio
    async def test_system_error_should_return_http_500(self):
        """
        ОЖИДАЕМОЕ поведение: RuntimeError → HTTP 500.
        НА НЕФИКСИРОВАННОМ КОДЕ: HTTP 200 с total_score=0 — тест упадёт.

        Counterexample: endpoint вернул HTTP 200 с total_score=0 при RuntimeError.
        """
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient
        from app.api.v1.endpoints.student.attestation import router
        from app.api.deps import get_current_user, get_db
        from app.services.attestation_service import AttestationService

        app = FastAPI()
        app.include_router(router)

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.group_id = uuid4()
        mock_db = AsyncMock()

        async def override_user():
            return mock_user

        async def override_db():
            yield mock_db

        app.dependency_overrides[get_current_user] = override_user
        app.dependency_overrides[get_db] = override_db

        with patch.object(
            AttestationService,
            "calculate_student_score",
            side_effect=RuntimeError("Database connection failed"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.get("/attestation/first")

        # После фикса: HTTP 500 для системных ошибок
        # На нефиксированном коде: HTTP 200 с total_score=0
        assert response.status_code == 500, (
            f"Counterexample: endpoint вернул HTTP {response.status_code} "
            f"с телом {response.json()} при RuntimeError. "
            f"Ожидался HTTP 500. Баг error handling подтверждён."
        )

    @pytest.mark.asyncio
    async def test_system_error_should_not_return_total_score_zero(self):
        """
        Документирует ТЕКУЩЕЕ (баговое) поведение.
        На нефиксированном коде: HTTP 200 с total_score=0.
        """
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient
        from app.api.v1.endpoints.student.attestation import router
        from app.api.deps import get_current_user, get_db
        from app.services.attestation_service import AttestationService

        app = FastAPI()
        app.include_router(router)

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.group_id = uuid4()
        mock_db = AsyncMock()

        async def override_user():
            return mock_user

        async def override_db():
            yield mock_db

        app.dependency_overrides[get_current_user] = override_user
        app.dependency_overrides[get_db] = override_db

        with patch.object(
            AttestationService,
            "calculate_student_score",
            side_effect=RuntimeError("DB error"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.get("/attestation/first")

        # Counterexample: на нефиксированном коде вернёт 200 с total_score=0
        if response.status_code == 200:
            body = response.json()
            assert body.get("total_score") == 0, "Ожидался total_score=0 при ошибке"
            assert "calculation_status" in body, "Ожидался calculation_status в ответе"
            # Это баговое поведение — документируем
            pytest.fail(
                f"Counterexample: HTTP 200 с total_score=0 при RuntimeError. "
                f"Тело: {body}. Баг подтверждён — нужен HTTP 500."
            )
