"""
Калькулятор баллов за посещаемость.

Формула аттестации (этот модуль):
    adjusted_expected = expected_lessons - excused_count
    points_per_lesson = max_attendance / adjusted_expected
    score = (present * 1.0 + late * late_coef + absent * absent_coef) * points_per_lesson

Отличие от формулы отчётов:
    Это intentional divergence attendance_contract_v1.
    В отчётах EXCUSED остаётся report/export presentation-маркером, а не attestation score slot.
    Семантика "нет записи посещаемости" = 0 баллов, 0 штрафа (запись отсутствует → не считается).
"""

from dataclasses import dataclass

from app.models.attendance import Attendance, AttendanceStatus
from app.models.attestation_settings import AttestationSettings
from app.services.attendance_contract import AttendanceCounts


@dataclass
class AttendanceScoreResult:
    """Результат расчёта баллов за посещаемость"""

    score: float  # Итоговые баллы
    max_score: float  # Максимум возможных баллов
    ratio: float  # Процент посещаемости (0-1)
    total_classes: int  # Всего занятий
    expected_lessons: int  # Ожидаемое количество занятий
    present_count: int
    late_count: int
    excused_count: int
    absent_count: int


class AttendanceScoreCalculator:
    """Калькулятор баллов за посещаемость (фиксированные баллы за занятие)"""

    def calculate(
        self,
        attendance_records: list[Attendance],
        settings: AttestationSettings,
        expected_lessons: int,
        transfer_attendance: dict = None,
    ) -> AttendanceScoreResult:
        """
        Расчёт баллов за посещаемость.

        Формула:
        - points_per_lesson = max_attendance / expected_lessons
        - score = (present + late * late_coef) * points_per_lesson

        Args:
            expected_lessons: Ожидаемое количество занятий (из Lesson или настроек)
            transfer_attendance: Снапшот посещаемости из переводов
        """
        max_score = settings.get_max_component_points(settings.attendance_weight)

        counts = AttendanceCounts.from_records(attendance_records, transfer_attendance)
        present_count = counts.present
        late_count = counts.late
        excused_count = counts.excused
        absent_count = counts.absent

        total_classes = present_count + late_count + excused_count + absent_count

        # Фиксированные баллы за занятие
        # EXCUSED не учитывается ни в числителе, ни в знаменателе:
        # adjusted_expected = expected_lessons - excused_count
        # Формула аттестации: score = effective / adjusted_expected * max
        # (отличие от отчётов: там EXCUSED включается в знаменатель)
        if expected_lessons <= 0:
            points_per_lesson = 0.0
            ratio = 0.0
            score = 0.0
        else:
            # Уменьшаем знаменатель на EXCUSED (уважительные пропуски не штрафуют)
            adjusted_expected = expected_lessons - excused_count
            if adjusted_expected <= 0:
                adjusted_expected = 0
            if adjusted_expected == 0 and excused_count > 0 and present_count == 0 and late_count == 0 and absent_count == 0:
                score = max_score
                ratio = 1.0
            else:
                if adjusted_expected <= 0:
                    adjusted_expected = expected_lessons  # защита от деления на 0
                points_per_lesson = max_score / adjusted_expected
                # Эффективная посещаемость с коэффициентами (EXCUSED не в числителе)
                effective_attendance = (
                    present_count * 1.0 + late_count * settings.late_coef + absent_count * settings.absent_coef
                )
                score = effective_attendance * points_per_lesson
                # Ratio — процент посещаемости без EXCUSED
                counted = present_count + late_count + absent_count
                ratio = effective_attendance / counted if counted > 0 else 0.0

        # Cap: минимум 0, максимум max_score
        score = max(0, min(score, max_score))
        # Ratio: ограничиваем 0-1, может быть отрицательным при absent_coef < 0
        ratio = max(0, min(ratio, 1.0))

        return AttendanceScoreResult(
            score=round(score, 2),
            max_score=max_score,
            ratio=round(ratio, 4),
            total_classes=total_classes,
            expected_lessons=expected_lessons,
            present_count=present_count,
            late_count=late_count,
            excused_count=excused_count,
            absent_count=absent_count,
        )
