"""
Калькулятор баллов за лабораторные работы.
"""
from typing import List

from app.models.attestation_settings import AttestationSettings
from app.models.submission import Submission, SubmissionStatus
from app.models.lab import Lab
from app.models.lesson_grade import LessonGrade

from .models import LabScoreResult
from .constants import MIN_GRADE, GRADE_RANGE


class LabScoreCalculator:
    """Калькулятор баллов за лабораторные работы."""
    
    def calculate_from_submissions(
        self,
        submissions: List[Submission],
        labs: List[Lab],
        settings: AttestationSettings
    ) -> LabScoreResult:
        """
        Расчёт баллов за лабораторные работы из Submission.
        
        Requirements:
        - 2.1: coefficient 1.0 for on-time submission
        - 2.2: coefficient 0.7 for soft deadline violation
        - 2.3: coefficient 0.5 for hard deadline violation
        - 2.4: coefficient 1.0 for excused late submission
        - 2.6: bonus points for extra labs
        - 2.7: multiply by labs weight percentage
        """
        accepted_submissions = [
            s for s in submissions 
            if s.status == SubmissionStatus.ACCEPTED
        ]
        
        labs_dict = {lab.id: lab for lab in labs}
        
        total_raw_score = 0.0
        submissions_details = []
        
        for submission in accepted_submissions:
            lab = labs_dict.get(submission.lab_id)
            if not lab:
                continue
            
            base_score = submission.grade if submission.grade is not None else lab.max_grade
            coefficient = self._calculate_deadline_coefficient(submission, lab, settings)
            lab_score = base_score * coefficient
            total_raw_score += lab_score
            
            submissions_details.append({
                'lab_id': str(lab.id),
                'lab_title': lab.title,
                'base_score': base_score,
                'coefficient': coefficient,
                'final_score': lab_score,
                'submitted_at': submission.created_at.isoformat() if submission.created_at else None,
                'deadline': lab.deadline.isoformat() if lab.deadline else None
            })
        
        labs_count = len(accepted_submissions)
        required_count = settings.required_labs_count
        
        bonus_points = 0.0
        if labs_count > required_count:
            extra_labs = labs_count - required_count
            bonus_points = extra_labs * settings.bonus_per_extra_lab
            total_raw_score += bonus_points
        
        weighted_score = (total_raw_score * settings.labs_weight / 100)
        
        return LabScoreResult(
            raw_score=total_raw_score,
            weighted_score=weighted_score,
            labs_count=labs_count,
            required_count=required_count,
            bonus_points=bonus_points,
            submissions_details=submissions_details
        )
    
    def _calculate_deadline_coefficient(
        self,
        submission: Submission,
        lab: Lab,
        settings: AttestationSettings
    ) -> float:
        """
        Расчёт коэффициента дедлайна для работы.
        
        Requirements:
        - 2.1: 1.0 for on-time
        - 2.2: soft_deadline_penalty for soft deadline violation
        - 2.3: hard_deadline_penalty for hard deadline violation
        - 2.4: 1.0 for excused (is_manual=True)
        """
        if not lab.deadline:
            return 1.0
        
        if submission.is_manual:
            return 1.0
        
        if not submission.created_at:
            return 1.0
        
        submission_date = submission.created_at
        deadline = lab.deadline
        
        # Приводим к одному типу для сравнения
        if submission_date.tzinfo is None and deadline.tzinfo is not None:
            submission_date = submission_date.replace(tzinfo=deadline.tzinfo)
        elif submission_date.tzinfo is not None and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=submission_date.tzinfo)
        
        if submission_date <= deadline:
            return 1.0
        
        days_late = (submission_date - deadline).days
        
        if days_late <= settings.soft_deadline_days:
            return settings.soft_deadline_penalty
        
        return settings.hard_deadline_penalty

    def calculate_from_lesson_grades(
        self,
        lesson_grades: List[LessonGrade],
        settings: AttestationSettings
    ) -> LabScoreResult:
        """
        Расчёт баллов за лабораторные на основе LessonGrade (оценки 2-5 из журнала).
        
        Логика:
        - Оценка 2 = 0%, 3 = 33%, 4 = 67%, 5 = 100%
        - Среднее нормализуется и умножается на labs_weight
        """
        if not lesson_grades:
            return LabScoreResult(
                raw_score=0.0,
                weighted_score=0.0,
                labs_count=0,
                required_count=settings.required_labs_count,
                bonus_points=0.0,
                submissions_details=[]
            )
        
        # Нормализуем оценки: (grade - MIN_GRADE) / GRADE_RANGE дает 0-1
        normalized_scores = [(g.grade - MIN_GRADE) / GRADE_RANGE for g in lesson_grades]
        avg_normalized = sum(normalized_scores) / len(normalized_scores)
        
        raw_score = avg_normalized * 100
        
        labs_count = len(lesson_grades)
        required_count = settings.required_labs_count
        
        bonus_points = 0.0
        if labs_count > required_count:
            extra_labs = labs_count - required_count
            bonus_points = extra_labs * settings.bonus_per_extra_lab
        
        weighted_score = (raw_score + bonus_points) * settings.labs_weight / 100
        
        details = [
            {
                'lesson_id': str(g.lesson_id),
                'work_number': g.work_number,
                'grade': g.grade,
                'normalized': (g.grade - MIN_GRADE) / GRADE_RANGE
            }
            for g in lesson_grades
        ]
        
        return LabScoreResult(
            raw_score=raw_score + bonus_points,
            weighted_score=weighted_score,
            labs_count=labs_count,
            required_count=required_count,
            bonus_points=bonus_points,
            submissions_details=details
        )
