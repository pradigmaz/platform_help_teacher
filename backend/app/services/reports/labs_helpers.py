"""
Хелперы для сбора данных лабораторных работ.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission, SubmissionStatus
from app.models.lab import Lab
from app.models.user import User
from app.models.attestation_settings import AttestationType
from app.schemas.report import LabProgress, LabSubmission
from app.services.attestation.settings import AttestationSettingsManager


async def get_group_labs_stats(
    db: AsyncSession,
    students: List[User],
    labs_count_override: Optional[int] = None
) -> Dict[UUID, Dict]:
    """Получить статистику лабораторных работ группы.
    
    Args:
        db: Сессия БД
        students: Список студентов
        labs_count_override: Переопределить количество лаб (из настроек аттестации)
    """
    student_ids = [s.id for s in students]
    
    # Если не передано количество лаб - берём из настроек аттестации
    if labs_count_override is not None:
        total_labs = labs_count_override
    else:
        settings_manager = AttestationSettingsManager(db)
        settings = await settings_manager.get_settings(AttestationType.FIRST)
        total_labs = settings.labs_count_first if settings else 8
    
    submissions_query = (
        select(Submission.user_id, func.count(Submission.id).label('count'))
        .where(
            Submission.user_id.in_(student_ids),
            Submission.status.in_([SubmissionStatus.ACCEPTED, SubmissionStatus.READY, SubmissionStatus.IN_REVIEW])
        )
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
    students: List[User],
    has_subgroups: bool = False
) -> tuple[List[LabProgress], Optional[Dict[str, List[LabProgress]]]]:
    """Получить прогресс по лабораторным работам.
    
    Returns:
        Tuple[all_progress, by_subgroup_dict или None]
    """
    student_ids = [s.id for s in students]
    total_students = len(students)
    
    labs_query = select(Lab).order_by(Lab.created_at)
    labs_result = await db.execute(labs_query)
    labs = list(labs_result.scalars().all())
    
    submissions_query = (
        select(Submission.lab_id, func.count(func.distinct(Submission.user_id)).label('count'))
        .where(
            Submission.user_id.in_(student_ids),
            Submission.status.in_([SubmissionStatus.ACCEPTED, SubmissionStatus.READY, SubmissionStatus.IN_REVIEW])
        )
        .group_by(Submission.lab_id)
    )
    submissions_result = await db.execute(submissions_query)
    submissions_map = {row.lab_id: row.count for row in submissions_result.all()}
    
    # Прогресс для всех
    progress_all = []
    for idx, lab in enumerate(labs, 1):
        completed = submissions_map.get(lab.id, 0)
        progress_all.append(LabProgress(
            lab_name=lab.title or f"Лаб. {idx}",
            completed_count=completed,
            total_students=total_students,
            completion_rate=round(completed / total_students * 100, 1) if total_students > 0 else 0
        ))
    
    if not has_subgroups:
        return progress_all, None
    
    # Прогресс по подгруппам
    by_subgroup: Dict[str, List[LabProgress]] = {"all": progress_all, "1": [], "2": []}
    
    for subgroup_num in [1, 2]:
        subgroup_students = [s for s in students if s.subgroup == subgroup_num]
        subgroup_ids = [s.id for s in subgroup_students]
        subgroup_total = len(subgroup_students)
        
        if subgroup_total == 0:
            by_subgroup[str(subgroup_num)] = []
            continue
        
        sub_query = (
            select(Submission.lab_id, func.count(func.distinct(Submission.user_id)).label('count'))
            .where(
                Submission.user_id.in_(subgroup_ids),
                Submission.status.in_([SubmissionStatus.ACCEPTED, SubmissionStatus.READY, SubmissionStatus.IN_REVIEW])
            )
            .group_by(Submission.lab_id)
        )
        sub_result = await db.execute(sub_query)
        sub_map = {row.lab_id: row.count for row in sub_result.all()}
        
        for idx, lab in enumerate(labs, 1):
            completed = sub_map.get(lab.id, 0)
            by_subgroup[str(subgroup_num)].append(LabProgress(
                lab_name=lab.title or f"Лаб. {idx}",
                completed_count=completed,
                total_students=subgroup_total,
                completion_rate=round(completed / subgroup_total * 100, 1) if subgroup_total > 0 else 0,
                subgroup=subgroup_num
            ))
    
    return progress_all, by_subgroup


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
        # Считаем сданной только если статус ACCEPTED, READY или IN_REVIEW
        is_submitted = submission is not None and submission.status.value in ("ACCEPTED", "READY", "IN_REVIEW")
        result.append(LabSubmission(
            lab_id=lab.id,
            lab_name=lab.title or f"Лабораторная {idx}",
            lab_number=idx,
            grade=submission.grade if submission else None,
            max_grade=lab.max_grade or 10,
            submitted_at=submission.submitted_at if submission and hasattr(submission, 'submitted_at') else None,
            is_submitted=is_submitted,
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
