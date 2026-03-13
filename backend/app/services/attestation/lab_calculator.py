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

    @staticmethod
    def _pick_external_grade(transfer_grade: dict | None, submission_grade: dict | None) -> tuple[str, dict] | None:
        if transfer_grade is None and submission_grade is None:
            return None
        if transfer_grade is None:
            return "submission", submission_grade
        if submission_grade is None:
            return "transfer", transfer_grade

        transfer_rank = (
            int(transfer_grade.get("grade", 0)),
            str(transfer_grade.get("updated_at") or transfer_grade.get("created_at") or ""),
        )
        submission_rank = (
            int(submission_grade.get("grade", 0)),
            str(submission_grade.get("accepted_at") or submission_grade.get("created_at") or ""),
        )
        if submission_rank >= transfer_rank:
            return "submission", submission_grade
        return "transfer", transfer_grade

    def calculate(
        self,
        lesson_grades: list[LessonGrade],
        settings: AttestationSettings,
        transfer_grades: list[dict] = None,
        submission_grades: list[dict] = None,
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
        normalized_submission: dict[tuple[str, int], dict] = {}

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

        if submission_grades:
            for sg in submission_grades:
                work_number = sg.get("work_number")
                if work_number is None:
                    continue
                subject_key = str(sg.get("subject_id") or "__legacy__")
                normalized_submission[(subject_key, int(work_number))] = sg

        all_keys = set(normalized_current) | set(normalized_transfer) | set(normalized_submission)

        for key in sorted(all_keys):
            current_grade = normalized_current.get(key)
            transfer_grade = normalized_transfer.get(key)
            submission_grade = normalized_submission.get(key)

            use_transfer = False
            if current_grade is not None and transfer_grade is not None:
                transfer_value = int(transfer_grade.get("grade", 0))
                use_transfer = transfer_value > current_grade.grade
            external_grade = self._pick_external_grade(transfer_grade, submission_grade)

            if current_grade is not None and not use_transfer:
                grade_value = current_grade.grade
                lesson_id = str(current_grade.lesson_id)
                source = "journal"
                subject_id = getattr(current_grade, "lab_subject_id", None)
            elif external_grade is not None:
                source, grade_payload = external_grade
                grade_value = int(grade_payload.get("grade", 0))
                lesson_id = grade_payload.get("lesson_id")
                subject_id = grade_payload.get("subject_id")
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
                    "from_transfer": source == "transfer",
                    "from_submission": source == "submission",
                    "source": source,
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
