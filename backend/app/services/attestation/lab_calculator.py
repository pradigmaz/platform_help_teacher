"""
Калькулятор баллов за лабораторные работы.
Автобалансировка: баллы = (max_component / work_count) * grade_coef
"""
from typing import List
from dataclasses import dataclass

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson_grade import LessonGrade


@dataclass
class LabScoreResult:
    """Результат расчёта баллов за лабы"""
    score: float           # Итоговые баллы
    max_score: float       # Максимум возможных баллов
    labs_count: int        # Количество сданных работ
    labs_required: int     # Требуемое количество
    needs_rework: int      # Работы с оценкой 2 (требуют исправления)
    details: List[dict]    # Детализация по работам


class LabScoreCalculator:
    """Калькулятор баллов за лабораторные (автобалансировка)"""
    
    def calculate(
        self,
        lesson_grades: List[LessonGrade],
        settings: AttestationSettings,
        transfer_grades: List[dict] = None
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
        needs_rework = 0
        details = []
        
        # Обрабатываем текущие оценки
        for grade in lesson_grades:
            coef = settings.get_grade_coef(grade.grade)
            points = points_per_work * coef
            total_score += points
            
            if grade.grade == 2:
                needs_rework += 1
            
            details.append({
                'lesson_id': str(grade.lesson_id),
                'work_number': grade.work_number,
                'grade': grade.grade,
                'coef': coef,
                'points': round(points, 2),
                'needs_rework': grade.grade == 2,
                'from_transfer': False
            })
        
        # Добавляем оценки из снапшотов переводов
        if transfer_grades:
            for tg in transfer_grades:
                grade_val = tg.get('grade', 0)
                coef = settings.get_grade_coef(grade_val)
                points = points_per_work * coef
                total_score += points
                
                if grade_val == 2:
                    needs_rework += 1
                
                details.append({
                    'lesson_id': tg.get('lesson_id'),
                    'work_number': tg.get('work_number', 0),
                    'grade': grade_val,
                    'coef': coef,
                    'points': round(points, 2),
                    'needs_rework': grade_val == 2,
                    'from_transfer': True
                })
        
        total_labs = len(lesson_grades) + (len(transfer_grades) if transfer_grades else 0)
        
        return LabScoreResult(
            score=min(total_score, max_score),  # Не больше максимума
            max_score=max_score,
            labs_count=total_labs,
            labs_required=labs_count,
            needs_rework=needs_rework,
            details=details
        )
