"""
Калькулятор баллов для аттестации.

Чистая логика расчёта без зависимостей от БД.
Реализует:
- Requirements 2.1-2.7: расчёт баллов за лабораторные с учётом дедлайнов
- Requirements 3.2-3.7: расчёт баллов за посещаемость
- Requirements 4.1-4.4: итоговый расчёт и перевод в оценки
"""
from typing import List

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.lab import Lab
from app.models.work import Work
from app.models.work_submission import WorkSubmission
from app.models.lesson_grade import LessonGrade

from .models import LabScoreResult, AttendanceScoreResult, WorkScoreResult


class AttestationCalculator:
    """
    Калькулятор баллов для аттестации.
    
    Stateless класс с чистыми функциями расчёта.
    """
    
    def calculate_lab_score(
        self,
        submissions: List[Submission],
        labs: List[Lab],
        settings: AttestationSettings
    ) -> LabScoreResult:
        """
        Расчёт баллов за лабораторные работы.
        
        Requirements:
        - 2.1: coefficient 1.0 for on-time submission
        - 2.2: coefficient 0.7 for soft deadline violation
        - 2.3: coefficient 0.5 for hard deadline violation
        - 2.4: coefficient 1.0 for excused late submission
        - 2.6: bonus points for extra labs
        - 2.7: multiply by labs weight percentage
        """
        # Фильтруем только принятые работы
        accepted_submissions = [
            s for s in submissions 
            if s.status == SubmissionStatus.ACCEPTED
        ]
        
        # Создаём словарь лаб для быстрого доступа
        labs_dict = {lab.id: lab for lab in labs}
        
        total_raw_score = 0.0
        submissions_details = []
        
        for submission in accepted_submissions:
            lab = labs_dict.get(submission.lab_id)
            if not lab:
                continue
            
            # Базовый балл за лабу (из оценки или max_grade)
            base_score = submission.grade if submission.grade is not None else lab.max_grade
            
            # Определяем коэффициент дедлайна
            coefficient = self._calculate_deadline_coefficient(
                submission=submission,
                lab=lab,
                settings=settings
            )
            
            # Итоговый балл за лабу
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
        
        # Бонус за дополнительные лабы (Requirements 2.6)
        bonus_points = 0.0
        if labs_count > required_count:
            extra_labs = labs_count - required_count
            bonus_points = extra_labs * settings.bonus_per_extra_lab
            total_raw_score += bonus_points
        
        # Взвешенный балл (Requirements 2.7)
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
        - 2.2: soft_deadline_penalty (default 0.7) for soft deadline violation
        - 2.3: hard_deadline_penalty (default 0.5) for hard deadline violation
        - 2.4: 1.0 for excused (is_manual=True считаем уважительной причиной)
        """
        # Если нет дедлайна - полный балл
        if not lab.deadline:
            return 1.0
        
        # Если ручная оценка - считаем уважительной причиной (Requirements 2.4)
        if submission.is_manual:
            return 1.0
        
        # Если нет даты создания - полный балл
        if not submission.created_at:
            return 1.0
        
        submission_date = submission.created_at
        deadline = lab.deadline
        
        # Приводим к одному типу для сравнения
        if submission_date.tzinfo is None and deadline.tzinfo is not None:
            submission_date = submission_date.replace(tzinfo=deadline.tzinfo)
        elif submission_date.tzinfo is not None and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=submission_date.tzinfo)
        
        # Сдано вовремя (Requirements 2.1)
        if submission_date <= deadline:
            return 1.0
        
        # Вычисляем просрочку в днях
        days_late = (submission_date - deadline).days
        
        # Мягкий дедлайн (Requirements 2.2)
        if days_late <= settings.soft_deadline_days:
            return settings.soft_deadline_penalty
        
        # Жёсткий дедлайн (Requirements 2.3)
        return settings.hard_deadline_penalty

    def calculate_lesson_grades_score(
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
        
        # Нормализуем оценки: (grade - 2) / 3 дает 0-1
        normalized_scores = [(g.grade - 2) / 3 for g in lesson_grades]
        avg_normalized = sum(normalized_scores) / len(normalized_scores)
        
        # Сырой балл = среднее * 100 (процент)
        raw_score = avg_normalized * 100
        
        labs_count = len(lesson_grades)
        required_count = settings.required_labs_count
        
        # Бонус за дополнительные лабы
        bonus_points = 0.0
        if labs_count > required_count:
            extra_labs = labs_count - required_count
            bonus_points = extra_labs * settings.bonus_per_extra_lab
        
        # Взвешенный балл
        weighted_score = (raw_score + bonus_points) * settings.labs_weight / 100
        
        details = [
            {
                'lesson_id': str(g.lesson_id),
                'work_number': g.work_number,
                'grade': g.grade,
                'normalized': (g.grade - 2) / 3
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
    
    def calculate_attendance_score(
        self,
        attendance_records: List[Attendance],
        settings: AttestationSettings
    ) -> AttendanceScoreResult:
        """
        Расчёт баллов за посещаемость.
        
        Requirements:
        - 3.2: points for PRESENT status
        - 3.3: points for LATE status
        - 3.4: points for EXCUSED status
        - 3.5: points for ABSENT status
        - 3.7: multiply by attendance weight percentage
        """
        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0
        
        raw_score = 0.0
        
        for record in attendance_records:
            if record.status == AttendanceStatus.PRESENT:
                present_count += 1
                raw_score += settings.present_points
            elif record.status == AttendanceStatus.LATE:
                late_count += 1
                raw_score += settings.late_points
            elif record.status == AttendanceStatus.EXCUSED:
                excused_count += 1
                raw_score += settings.excused_points
            elif record.status == AttendanceStatus.ABSENT:
                absent_count += 1
                raw_score += settings.absent_points
        
        total_classes = len(attendance_records)
        
        # Нормализуем балл (если есть занятия)
        if total_classes > 0:
            max_attendance_score = total_classes * settings.present_points
            if max_attendance_score > 0:
                normalized_score = (raw_score / max_attendance_score) * 100
                normalized_score = max(0, normalized_score)
            else:
                normalized_score = 0
        else:
            normalized_score = 0
        
        # Взвешенный балл (Requirements 3.7)
        max_points = AttestationSettings.get_max_points(settings.attestation_type)
        weighted_score = (normalized_score * settings.attendance_weight / 100) * (max_points / 100)
        
        return AttendanceScoreResult(
            raw_score=raw_score,
            weighted_score=weighted_score,
            total_classes=total_classes,
            present_count=present_count,
            late_count=late_count,
            excused_count=excused_count,
            absent_count=absent_count
        )
    
    def calculate_activity_score(
        self,
        activity_points: float,
        settings: AttestationSettings
    ) -> float:
        """Расчёт баллов за активность."""
        if not settings.activity_enabled:
            return 0.0
        
        weighted_score = (activity_points * settings.activity_weight / 100)
        return weighted_score

    def calculate_work_score(
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
    
    def calculate_total_score(
        self,
        lab_result: LabScoreResult,
        attendance_result: AttendanceScoreResult,
        activity_score: float,
        settings: AttestationSettings
    ) -> tuple[float, str, bool]:
        """
        Расчёт итогового балла и оценки.
        
        Requirements:
        - 4.1: sum weighted components
        - 4.2: cap at max points (35 for first, 70 for second)
        - 4.3, 4.4: convert to grade using fixed university scales
        """
        # Суммируем взвешенные компоненты (Requirements 4.1)
        total = (
            lab_result.weighted_score +
            attendance_result.weighted_score +
            activity_score
        )
        
        # Ограничиваем максимальными баллами (Requirements 4.2)
        max_points = AttestationSettings.get_max_points(settings.attestation_type)
        total = min(total, max_points)
        total = max(0, total)
        
        # Переводим в оценку (Requirements 4.3, 4.4)
        grade = self._convert_to_grade(total, settings.attestation_type)
        
        # Проверяем зачёт
        min_passing = AttestationSettings.get_min_passing_points(settings.attestation_type)
        is_passing = total >= min_passing
        
        return total, grade, is_passing
    
    def _convert_to_grade(self, score: float, attestation_type: AttestationType) -> str:
        """
        Перевод балла в оценку по фиксированной шкале университета.
        
        Requirements 4.3, 4.4:
        - First attestation: 1-19.99=неуд, 20-25=уд, 26-30=хор, 31-35=отл
        - Second attestation: 1-39.99=неуд, 40-50=уд, 51-60=хор, 61-70=отл
        """
        grade_scale = AttestationSettings.get_grade_scale(attestation_type)
        
        for grade_name, (min_val, max_val) in grade_scale.items():
            if min_val <= score <= max_val:
                return grade_name
        
        # Если балл выше максимума - отлично
        if score > AttestationSettings.get_max_points(attestation_type):
            return "отл"
        
        return "неуд"
