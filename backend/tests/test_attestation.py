"""
Тесты для модуля Attestation (аттестация).
Критические тесты для валидации расчётов и бизнес-логики.
"""
import pytest
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

import sys
sys.path.insert(0, '/app')

from app.models.attestation_settings import AttestationType, AttestationSettings
from app.schemas.attestation import (
    AttestationSettingsBase,
    AttestationSettingsUpdate,
)
from app.services.attestation.constants import MIN_GRADE, MAX_GRADE, GRADE_RANGE


# ============== Grade Boundaries Tests ==============

class TestGradeBoundaries:
    """Тесты граничных значений оценок (2-5)."""

    def test_grade_constants(self):
        """Тест констант оценок."""
        assert MIN_GRADE == 2
        assert MAX_GRADE == 5
        assert GRADE_RANGE == 3

    def test_normalized_score_at_min_grade(self):
        """Тест нормализации при минимальной оценке (2)."""
        grade = MIN_GRADE
        normalized = (grade - MIN_GRADE) / GRADE_RANGE
        assert normalized == 0.0

    def test_normalized_score_at_max_grade(self):
        """Тест нормализации при максимальной оценке (5)."""
        grade = MAX_GRADE
        normalized = (grade - MIN_GRADE) / GRADE_RANGE
        assert normalized == 1.0

    def test_normalized_score_at_middle_grade(self):
        """Тест нормализации при средней оценке (3.5)."""
        grade = 3.5
        normalized = (grade - MIN_GRADE) / GRADE_RANGE
        assert abs(normalized - 0.5) < 0.01

    def test_grade_below_min_gives_negative(self):
        """Тест что оценка ниже 2 даёт отрицательный результат."""
        grade = 1
        normalized = (grade - MIN_GRADE) / GRADE_RANGE
        assert normalized < 0

    def test_grade_above_max_gives_over_100(self):
        """Тест что оценка выше 5 даёт >100%."""
        grade = 6
        normalized = (grade - MIN_GRADE) / GRADE_RANGE
        assert normalized > 1.0


# ============== Weights Validation Tests ==============

class TestWeightsValidation:
    """Тесты валидации суммы базовых весов = 100%."""

    def test_valid_weights_sum_100(self):
        """Тест валидных весов (сумма = 100%)."""
        settings = AttestationSettingsBase(
            labs_weight=70.0,
            attendance_weight=30.0,
            activity_reserve=10.0
        )
        assert settings.labs_weight + settings.attendance_weight == 100.0
        assert settings.activity_reserve == 10.0

    def test_invalid_weights_sum_less_than_100(self):
        """Тест невалидных весов (сумма < 100%)."""
        with pytest.raises(ValidationError, match="100%"):
            AttestationSettingsBase(
                labs_weight=50.0,
                attendance_weight=20.0,
                activity_reserve=10.0
            )

    def test_invalid_weights_sum_more_than_100(self):
        """Тест невалидных весов (сумма > 100%)."""
        with pytest.raises(ValidationError, match="100%"):
            AttestationSettingsBase(
                labs_weight=80.0,
                attendance_weight=30.0,
                activity_reserve=10.0
            )

    def test_weights_with_small_tolerance(self):
        """Тест весов с малой погрешностью (99.99 ≈ 100)."""
        # Должно пройти из-за tolerance 0.01
        settings = AttestationSettingsBase(
            labs_weight=69.995,
            attendance_weight=30.0,
            activity_reserve=10.0
        )
        total = settings.labs_weight + settings.attendance_weight
        assert abs(total - 100.0) < 0.01

    def test_model_validate_weights(self):
        """Тест метода validate_weights модели."""
        att_settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=30.0,
            activity_reserve=10.0
        )
        assert att_settings.validate_weights() is True

        att_settings.labs_weight = 50.0
        assert att_settings.validate_weights() is False


# ============== Period Date Validation Tests ==============

class TestPeriodDateValidation:
    """Тесты валидации period_start_date < period_end_date."""

    def test_valid_period_dates(self):
        """Тест валидных дат периода."""
        settings = AttestationSettingsBase(
            period_start_date=date(2025, 9, 1),
            period_end_date=date(2025, 10, 15)
        )
        assert settings.period_start_date < settings.period_end_date

    def test_invalid_period_dates_start_after_end(self):
        """Тест невалидных дат (start > end)."""
        with pytest.raises(ValidationError, match="period_start_date"):
            AttestationSettingsBase(
                period_start_date=date(2025, 10, 15),
                period_end_date=date(2025, 9, 1)
            )

    def test_same_start_and_end_date(self):
        """Тест одинаковых дат (start == end) — должно быть валидно."""
        settings = AttestationSettingsBase(
            period_start_date=date(2025, 10, 1),
            period_end_date=date(2025, 10, 1)
        )
        assert settings.period_start_date == settings.period_end_date

    def test_null_period_dates(self):
        """Тест null дат периода — должно быть валидно."""
        settings = AttestationSettingsBase(
            period_start_date=None,
            period_end_date=None
        )
        assert settings.period_start_date is None
        assert settings.period_end_date is None

    def test_partial_period_dates(self):
        """Тест частичных дат (только start или только end)."""
        settings1 = AttestationSettingsBase(period_start_date=date(2025, 9, 1))
        assert settings1.period_start_date is not None
        assert settings1.period_end_date is None

        settings2 = AttestationSettingsBase(period_end_date=date(2025, 10, 15))
        assert settings2.period_start_date is None
        assert settings2.period_end_date is not None


# ============== Grade Scale Conversion Tests ==============

class TestGradeScaleConversion:
    """Тесты перевода баллов в оценки."""

    def test_first_attestation_grade_scale(self):
        """Тест шкалы оценок первой аттестации (макс 35)."""
        scale = AttestationSettings.get_grade_scale(AttestationType.FIRST)

        assert scale["неуд"] == (0, 20)
        assert scale["уд"] == (20, 26)
        assert scale["хор"] == (26, 31)
        assert scale["отл"] == (31, 35)

    def test_second_attestation_grade_scale(self):
        """Тест шкалы оценок второй аттестации (макс 70)."""
        scale = AttestationSettings.get_grade_scale(AttestationType.SECOND)

        assert scale["неуд"] == (0, 40)
        assert scale["уд"] == (40, 51)
        assert scale["хор"] == (51, 61)
        assert scale["отл"] == (61, 70)

    def test_max_points_first_attestation(self):
        """Тест максимальных баллов первой аттестации."""
        max_points = AttestationSettings.get_max_points(AttestationType.FIRST)
        assert max_points == 35

    def test_max_points_second_attestation(self):
        """Тест максимальных баллов второй аттестации."""
        max_points = AttestationSettings.get_max_points(AttestationType.SECOND)
        assert max_points == 70

    def test_min_passing_first_attestation(self):
        """Тест минимальных баллов для зачёта первой аттестации."""
        min_passing = AttestationSettings.get_min_passing_points(AttestationType.FIRST)
        assert min_passing == 20

    def test_min_passing_second_attestation(self):
        """Тест минимальных баллов для зачёта второй аттестации."""
        min_passing = AttestationSettings.get_min_passing_points(AttestationType.SECOND)
        assert min_passing == 40

    def test_grade_boundaries_first_attestation(self):
        """Тест граничных значений оценок первой аттестации."""
        scale = AttestationSettings.get_grade_scale(AttestationType.FIRST)

        # Граница неуд/уд: интервалы [lower, upper) для всех кроме последнего
        assert 20 == scale["неуд"][1]
        assert 20 == scale["уд"][0]

        # Граница уд/хор
        assert 26 == scale["уд"][1]
        assert 26 == scale["хор"][0]

        # Граница хор/отл
        assert 31 == scale["хор"][1]
        assert 31 == scale["отл"][0]

    def test_grade_boundaries_second_attestation(self):
        """Тест граничных значений оценок второй аттестации."""
        scale = AttestationSettings.get_grade_scale(AttestationType.SECOND)

        # Граница неуд/уд: интервалы [lower, upper) для всех кроме последнего
        assert 40 == scale["неуд"][1]
        assert 40 == scale["уд"][0]

        # Граница уд/хор
        assert 51 == scale["уд"][1]
        assert 51 == scale["хор"][0]

        # Граница хор/отл
        assert 61 == scale["хор"][1]
        assert 61 == scale["отл"][0]


# ============== Transfer Validation Tests ==============

class TestTransferValidation:
    """Тесты валидации переводов студентов."""

    @pytest.mark.asyncio
    async def test_transfer_blocked_after_period_end(self):
        """Тест что перевод блокируется после окончания периода аттестации."""
        from app.services.transfer_service import TransferService
        
        mock_db = AsyncMock()
        service = TransferService(mock_db)
        
        # Мокаем настройки с прошедшей датой окончания
        past_date = date.today() - timedelta(days=1)
        mock_settings = MagicMock()
        mock_settings.period_end_date = past_date
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_settings
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ValueError, match="завершён"):
            await service._validate_attestation_period(AttestationType.FIRST)

    @pytest.mark.asyncio
    async def test_transfer_allowed_before_period_end(self):
        """Тест что перевод разрешён до окончания периода."""
        from app.services.transfer_service import TransferService
        
        mock_db = AsyncMock()
        service = TransferService(mock_db)
        
        # Мокаем настройки с будущей датой окончания
        future_date = date.today() + timedelta(days=7)
        mock_settings = MagicMock()
        mock_settings.period_end_date = future_date
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_settings
        mock_db.execute.return_value = mock_result
        
        # Не должно выбросить исключение
        await service._validate_attestation_period(AttestationType.FIRST)

    @pytest.mark.asyncio
    async def test_transfer_allowed_when_no_period_set(self):
        """Тест что перевод разрешён когда период не установлен."""
        from app.services.transfer_service import TransferService
        
        mock_db = AsyncMock()
        service = TransferService(mock_db)
        
        # Мокаем настройки без даты окончания
        mock_settings = MagicMock()
        mock_settings.period_end_date = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_settings
        mock_db.execute.return_value = mock_result
        
        # Не должно выбросить исключение
        await service._validate_attestation_period(AttestationType.FIRST)


# ============== Batch Calculation Consistency Tests ==============

class TestBatchCalculationConsistency:
    """Тесты консистентности batch расчётов."""

    def test_settings_snapshot_concept(self):
        """Тест концепции снапшота настроек."""
        # Создаём настройки
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0
        )
        
        # Создаём снапшот (копию значений)
        snapshot = {
            'labs_weight': settings.labs_weight,
            'attendance_weight': settings.attendance_weight,
            'activity_reserve': settings.activity_reserve
        }
        
        # Изменяем оригинал
        settings.labs_weight = 60.0
        
        # Снапшот должен остаться неизменным
        assert snapshot['labs_weight'] == 70.0
        assert settings.labs_weight == 60.0


# ============== Subgroup Filtering Tests ==============

class TestSubgroupFiltering:
    """Тесты фильтрации занятий по подгруппам."""

    def test_subgroup_filtering_logic_with_subgroup(self):
        """Тест логики фильтрации для студента с подгруппой."""
        # Симуляция логики фильтрации
        lessons = [
            {'id': 1, 'subgroup': None},  # Для всех
            {'id': 2, 'subgroup': 1},     # Подгруппа 1
            {'id': 3, 'subgroup': 2},     # Подгруппа 2
        ]
        student_subgroup = 1
        
        # Логика: subgroup is None OR subgroup == student_subgroup
        filtered = [
            l for l in lessons 
            if l['subgroup'] is None or l['subgroup'] == student_subgroup
        ]
        
        assert len(filtered) == 2
        assert {'id': 1, 'subgroup': None} in filtered
        assert {'id': 2, 'subgroup': 1} in filtered
        assert {'id': 3, 'subgroup': 2} not in filtered

    def test_subgroup_filtering_logic_without_subgroup(self):
        """Тест логики фильтрации для студента без подгруппы."""
        lessons = [
            {'id': 1, 'subgroup': None},
            {'id': 2, 'subgroup': 1},
            {'id': 3, 'subgroup': 2},
        ]
        student_subgroup = None
        
        # Логика: только subgroup is None
        filtered = [l for l in lessons if l['subgroup'] is None]
        
        assert len(filtered) == 1
        assert {'id': 1, 'subgroup': None} in filtered

    def test_subgroup_filtering_all_common_lessons(self):
        """Тест когда все занятия общие."""
        lessons = [
            {'id': 1, 'subgroup': None},
            {'id': 2, 'subgroup': None},
        ]
        
        # Любой студент видит все
        for sg in [None, 1, 2]:
            if sg is not None:
                filtered = [
                    l for l in lessons 
                    if l['subgroup'] is None or l['subgroup'] == sg
                ]
            else:
                filtered = [l for l in lessons if l['subgroup'] is None]
            assert len(filtered) == 2


# ============== Transfer Snapshot Merge Tests ==============

class TestTransferSnapshotMerge:
    """Тесты merge оценок при переводе."""

    def test_merge_uses_max_grade(self):
        """Тест что merge использует max(old, new)."""
        # Симуляция логики merge из student_score.py
        old_grades = {1: 4, 2: 5, 3: 3}  # work_number -> grade
        new_grades = {1: 3, 2: 5, 4: 4}  # work_number -> grade
        
        # Merge с max
        merged = dict(old_grades)
        for work_num, new_grade in new_grades.items():
            if work_num in merged:
                merged[work_num] = max(merged[work_num], new_grade)
            else:
                merged[work_num] = new_grade
        
        # Проверки
        assert merged[1] == 4  # max(4, 3) = 4
        assert merged[2] == 5  # max(5, 5) = 5
        assert merged[3] == 3  # только старая
        assert merged[4] == 4  # только новая

    def test_merge_preserves_better_old_grade(self):
        """Тест что merge сохраняет лучшую старую оценку."""
        old_grade = 5
        new_grade = 3
        merged = max(old_grade, new_grade)
        assert merged == 5

    def test_merge_takes_better_new_grade(self):
        """Тест что merge берёт лучшую новую оценку."""
        old_grade = 3
        new_grade = 5
        merged = max(old_grade, new_grade)
        assert merged == 5


# ============== Attestation Type Tests ==============

class TestAttestationType:
    """Тесты enum AttestationType."""

    def test_attestation_type_values(self):
        """Тест значений enum."""
        assert AttestationType.FIRST.value == "first"
        assert AttestationType.SECOND.value == "second"

    def test_attestation_type_number(self):
        """Тест свойства number."""
        assert AttestationType.FIRST.number == 1
        assert AttestationType.SECOND.number == 2

    def test_attestation_type_from_string(self):
        """Тест создания из строки."""
        first = AttestationType("first")
        second = AttestationType("second")
        
        assert first == AttestationType.FIRST
        assert second == AttestationType.SECOND

    def test_invalid_attestation_type(self):
        """Тест невалидного типа аттестации."""
        with pytest.raises(ValueError):
            AttestationType("third")


# ============== Security Tests ==============

class TestSecurityChecklist:
    """Тесты security checklist."""

    def test_grade_range_constraint_exists(self):
        """Тест что constraint на grade существует в константах."""
        assert MIN_GRADE == 2
        assert MAX_GRADE == 5
        # Constraint добавлен в миграции 044

    def test_period_dates_validation_exists(self):
        """Тест что валидация дат периода существует."""
        with pytest.raises(ValidationError):
            AttestationSettingsBase(
                period_start_date=date(2025, 12, 31),
                period_end_date=date(2025, 1, 1)
            )

    def test_weights_validation_exists(self):
        """Тест что валидация весов существует."""
        with pytest.raises(ValidationError):
            AttestationSettingsBase(
                labs_weight=75.0,
                attendance_weight=50.0,
                activity_reserve=50.0  # Сумма 150%
            )
