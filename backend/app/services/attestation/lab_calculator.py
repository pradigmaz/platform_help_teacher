"""
Калькулятор баллов за лабораторные работы.
Автобалансировка: баллы = (max_component / work_count) * grade_coef
"""

from dataclasses import dataclass

from app.models.attestation_settings import AttestationSettings
from app.models.lesson_grade import LessonGrade

from .lab_progress import get_lesson_grade_subject_key, is_completed_lab_grade


@dataclass
class LabScoreResult:
    """Результат расчёта баллов за лабы"""

    score: float  # Итоговые баллы
    max_score: float  # Максимум возможных баллов
    labs_count: int  # Количество сданных работ
    labs_required: int  # Требуемое количество
    needs_rework: int  # Работы с оценкой 2 (требуют исправления)
    details: list[dict]  # Детализация по работам


class LabScoreCalculator:
    """Калькулятор баллов за лабораторные (автобалансировка)"""

    def calculate(
        self, lesson_grades: list[LessonGrade], settings: AttestationSettings, transfer_grades: list[dict] = None
    ) -> LabScoreResult:
        """
        Расчёт баллов за лабораторные.

        Формула:
        - max_component = attestation_max * (labs_weight / 100)
        - points_per_work = max_component / labs_count
        - work_points = points_per_work * grade_coef

        Оценка 2:
        - grade_coef = 0 → 0 баллов
        - Работа помечается "требует исправления"

        Args:
            transfer_grades: Снапшоты оценок из переводов [{work_number, grade, lesson_id?}]
        """
        labs_count = settings.get_labs_count()
        max_score = settings.get_max_component_points(settings.labs_weight)
        points_per_work = settings.get_points_per_work(settings.labs_weight, labs_count)

        total_score = 0.0
        completed_labs = 0
        needs_rework = 0
        details = []
        normalized_current: dict[tuple[str, int], LessonGrade] = {}
        normalized_transfer: dict[tuple[str, int], dict] = {}

        # Обрабатываем текущие оценки
        for grade in lesson_grades:
            if grade.work_number is None:
                continue
            normalized_current[(get_lesson_grade_subject_key(grade), grade.work_number)] = grade

        # Добавляем оценки из снапшотов переводов
        if transfer_grades:
            for tg in transfer_grades:
                work_number = tg.get("work_number")
                if work_number is None:
                    continue
                subject_key = str(tg.get("subject_id") or "__legacy__")
                normalized_transfer[(subject_key, int(work_number))] = tg

        all_keys = set(normalized_current) | set(normalized_transfer)

        for key in sorted(all_keys):
            current_grade = normalized_current.get(key)
            transfer_grade = normalized_transfer.get(key)

            use_transfer = False
            if current_grade is not None and transfer_grade is not None:
                transfer_value = int(transfer_grade.get("grade", 0))
                use_transfer = transfer_value > current_grade.grade
            elif current_grade is None and transfer_grade is not None:
                use_transfer = True

            if current_grade is not None and not use_transfer:
                grade_value = current_grade.grade
                lesson_id = str(current_grade.lesson_id)
                from_transfer = False
                subject_id = getattr(current_grade, "lab_subject_id", None)
            elif transfer_grade is not None:
                grade_value = int(transfer_grade.get("grade", 0))
                lesson_id = transfer_grade.get("lesson_id")
                from_transfer = True
                subject_id = transfer_grade.get("subject_id")
            else:
                continue

            coef = settings.get_grade_coef(grade_value)
            points = points_per_work * coef
            total_score += points

            if grade_value == 2:
                needs_rework += 1
            elif is_completed_lab_grade(grade_value):
                completed_labs += 1

            details.append(
                {
                    "lesson_id": lesson_id,
                    "subject_id": str(subject_id) if subject_id else None,
                    "work_number": key[1],
                    "grade": grade_value,
                    "coef": coef,
                    "points": round(points, 2),
                    "needs_rework": grade_value == 2,
                    "from_transfer": from_transfer,
                }
            )

        return LabScoreResult(
            score=min(total_score, max_score),  # Не больше максимума
            max_score=max_score,
            labs_count=completed_labs,
            labs_required=labs_count,
            needs_rework=needs_rework,
            details=details,
        )
