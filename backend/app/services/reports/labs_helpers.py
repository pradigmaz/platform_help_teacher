"""
Хелперы для сбора данных лабораторных работ.
"""
from typing import List, Dict, Any
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission
from app.models.lab import Lab
from app.models.user import User
from app.schemas.report import LabProgress, LabSubmission


async def get_group_labs_stats(
    db: AsyncSession,
    students: List[User]
) -> Dict[UUID, Dict]:
    """Получить статистику лабораторных работ группы."""
    student_ids = [s.id for s in students]
    
    labs_query = select(Lab)
    labs_result = await db.execute(labs_query)
    labs = list(labs_result.scalars().all())
    total_labs = len(labs)
    
    submissions_query = (
        select(Submission.user_id, func.count(Submission.id).label('count'))
        .where(Submission.user_id.in_(student_ids))
        .group_by(Submission.user_id)
    )
    submissions_result = await db.execute(submissions_query)
    
    stats = {}
    for row in submissions_result.all():
        stats[row.user_id] = {'completed': row.count, 'total': total_labs}
    
    for student in students:
        if student.id not in stats:
            stats[student.id] = {'completed': 0, 'total': total_labs}
    
    return stats


async def get_lab_progress(
    db: AsyncSession,
    students: List[User]
) -> List[LabProgress]:
    """Получить прогресс по лабораторным работам."""
    student_ids = [s.id for s in students]
    total_students = len(students)
    
    labs_query = select(Lab).order_by(Lab.created_at)
    labs_result = await db.execute(labs_query)
    labs = list(labs_result.scalars().all())
    
    submissions_query = (
        select(Submission.lab_id, func.count(func.distinct(Submission.user_id)).label('count'))
        .where(Submission.user_id.in_(student_ids))
        .group_by(Submission.lab_id)
    )
    submissions_result = await db.execute(submissions_query)
    submissions_map = {row.lab_id: row.count for row in submissions_result.all()}
    
    progress = []
    for idx, lab in enumerate(labs, 1):
        completed = submissions_map.get(lab.id, 0)
        progress.append(LabProgress(
            lab_name=lab.title or f"Лаб. {idx}",
            completed_count=completed,
            total_students=total_students,
            completion_rate=round(completed / total_students * 100, 1) if total_students > 0 else 0
        ))
    
    return progress


async def get_student_lab_submissions(
    db: AsyncSession,
    student_id: UUID
) -> List[LabSubmission]:
    """Получить сдачи лабораторных работ студента."""
    labs_query = select(Lab).order_by(Lab.created_at)
    labs_result = await db.execute(labs_query)
    labs = list(labs_result.scalars().all())
    
    submissions_query = select(Submission).where(Submission.user_id == student_id)
    submissions_result = await db.execute(submissions_query)
    submissions = {s.lab_id: s for s in submissions_result.scalars().all()}
    
    result = []
    for idx, lab in enumerate(labs, 1):
        submission = submissions.get(lab.id)
        result.append(LabSubmission(
            lab_id=lab.id,
            lab_name=lab.title or f"Лабораторная {idx}",
            lab_number=idx,
            grade=submission.grade if submission else None,
            max_grade=lab.max_grade or 10,
            submitted_at=submission.submitted_at if submission and hasattr(submission, 'submitted_at') else None,
            is_submitted=submission is not None,
            is_late=False
        ))
    
    return result


def calculate_grade_distribution(results: List[Any]) -> Dict[str, int]:
    """Рассчитать распределение оценок."""
    distribution = defaultdict(int)
    for result in results:
        if result.grade:
            distribution[result.grade] += 1
    return dict(distribution)
