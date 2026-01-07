"""
Калькулятор баллов за работы (контрольные/самостоятельные/коллоквиумы/проект).
"""
from typing import List

from app.models.work import Work
from app.models.work_submission import WorkSubmission

from .models import WorkScoreResult


class WorkScoreCalculator:
    """Калькулятор баллов за работы."""
    
    def calculate(
        self,
        submissions: List[WorkSubmission],
        works: List[Work],
        weight: float,
        grading_scale: int = 10
    ) -> WorkScoreResult:
        """
        Расчёт баллов за работы (контрольные/самостоятельные/коллоквиумы/проект).
        """
        if not works or weight <= 0:
            return WorkScoreResult(0.0, 0.0, 0, len(works), [])
        
        works_dict = {w.id: w for w in works}
        total_score = 0.0
        details = []
        graded_count = 0
        
        for submission in submissions:
            work = works_dict.get(submission.work_id)
            if not work or submission.grade is None:
                continue
            
            graded_count += 1
            total_score += submission.grade
            details.append({
                'work_id': str(work.id),
                'work_title': work.title,
                'grade': submission.grade,
                'max_grade': work.max_grade
            })
        
        # Средний балл нормализованный к 100
        if graded_count > 0:
            avg_grade = total_score / graded_count
            normalized = (avg_grade / grading_scale) * 100
        else:
            normalized = 0.0
        
        weighted = (normalized / 100) * weight
        
        return WorkScoreResult(
            raw_score=normalized,
            weighted_score=weighted,
            count=graded_count,
            max_count=len(works),
            submissions_details=details
        )
