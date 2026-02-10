"""
Калькулятор баллов за посещаемость.
Фиксированные баллы за занятие: points_per_lesson = max_attendance / expected_lessons
"""
from dataclasses import dataclass

from app.models.attendance import Attendance, AttendanceStatus
from app.models.attestation_settings import AttestationSettings


@dataclass
class AttendanceScoreResult:
    """Результат расчёта баллов за посещаемость"""
    score: float           # Итоговые баллы
    max_score: float       # Максимум возможных баллов
    ratio: float           # Процент посещаемости (0-1)
    total_classes: int     # Всего занятий
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
        transfer_attendance: dict = None
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

        # Подсчёт из текущих записей
        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0

        for record in attendance_records:
            if record.status == AttendanceStatus.PRESENT:
                present_count += 1
            elif record.status == AttendanceStatus.LATE:
                late_count += 1
            elif record.status == AttendanceStatus.EXCUSED:
                excused_count += 1
            elif record.status == AttendanceStatus.ABSENT:
                absent_count += 1

        # Добавляем данные из снапшотов переводов
        if transfer_attendance:
            present_count += transfer_attendance.get("present", 0)
            late_count += transfer_attendance.get("late", 0)
            excused_count += transfer_attendance.get("excused", 0)
            absent_count += transfer_attendance.get("absent", 0)

        total_classes = present_count + late_count + excused_count + absent_count

        # Фиксированные баллы за занятие
        if expected_lessons <= 0:
            points_per_lesson = 0.0
            ratio = 0.0
            score = 0.0
        else:
            points_per_lesson = max_score / expected_lessons
            # Эффективная посещаемость с коэффициентами
            effective_attendance = (
                present_count * 1.0 +
                late_count * settings.late_coef +
                absent_count * settings.absent_coef
            )
            score = effective_attendance * points_per_lesson
            # Ratio — реальный процент посещаемости с учётом коэффициентов
            # Максимум = количество отмеченных занятий (если бы все были PRESENT)
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
            absent_count=absent_count
        )
