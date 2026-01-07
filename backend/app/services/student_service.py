from uuid import UUID
from datetime import datetime as dt, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Group, Lab, Submission, SubmissionStatus
from app.schemas.student import StudentProfileOut, StudentStats, StudentLabSubmission

class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, student_id: UUID) -> Optional[StudentProfileOut]:
        """
        Получить профиль студента с его лабораторными работами и статистикой.
        """
        # Получаем студента
        result = await self.db.execute(
            select(User).where(User.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            return None
        
        # Получаем группу студента
        group_name = None
        group_students = []
        if student.group_id:
            group_result = await self.db.execute(select(Group).where(Group.id == student.group_id))
            group = group_result.scalar_one_or_none()
            if group:
                group_name = group.name
            # Получаем всех студентов группы для сравнения
            students_result = await self.db.execute(
                select(User).where(User.group_id == student.group_id, User.role == "student")
            )
            group_students = students_result.scalars().all()
        
        # Получаем все лабы
        labs_result = await self.db.execute(select(Lab).order_by(Lab.created_at.desc()))
        labs = labs_result.scalars().all()
        
        # Получаем сдачи студента
        subs_result = await self.db.execute(
            select(Submission).where(Submission.user_id == student_id)
        )
        submissions = subs_result.scalars().all()
        subs_map = {sub.lab_id: sub for sub in submissions}
        
        # Собираем данные по лабам и статистику
        labs_data, stats = self._calculate_stats(labs, subs_map)
        
        # Рейтинг в группе
        if group_students:
            stats.group_total = len(group_students)
            
            # Optimization: Calculate all scores in one query to avoid N+1
            group_student_ids = [gs.id for gs in group_students]
            
            # Получаем сумму баллов для каждого студента группы одним запросом
            scores_query = (
                select(Submission.user_id, func.sum(Submission.grade))
                .where(
                    Submission.user_id.in_(group_student_ids),
                    Submission.status == SubmissionStatus.ACCEPTED
                )
                .group_by(Submission.user_id)
            )
            scores_result = await self.db.execute(scores_query)
            scores_map = {uid: (total or 0) for uid, total in scores_result.all()}
            
            # Формируем список (id, points) для всех студентов
            student_scores = []
            for gs in group_students:
                points = scores_map.get(gs.id, 0)
                student_scores.append((gs.id, points))
            
            # Сортируем по убыванию баллов
            student_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Находим баллы текущего студента
            current_student_points = None
            for sid, points in student_scores:
                if sid == student_id:
                    current_student_points = points
                    break
            
            if current_student_points is not None:
                # Место = количество студентов с баллами строго больше + 1
                stats.group_rank = sum(1 for _, p in student_scores if p > current_student_points) + 1
            
            # Процентиль (сколько студентов ниже)
            if stats.group_rank and stats.group_total > 1:
                stats.group_percentile = round(
                    ((stats.group_total - stats.group_rank) / (stats.group_total - 1)) * 100, 1
                ) 

        return StudentProfileOut(
            id=student.id,
            full_name=student.full_name,
            username=student.username,
            telegram_id=student.telegram_id,
            vk_id=student.vk_id,
            group_name=group_name,
            group_id=student.group_id,
            is_active=student.is_active,
            created_at=student.created_at,
            labs=labs_data,
            stats=stats,
        )

    def _calculate_stats(self, labs: List[Lab], subs_map: dict) -> Tuple[List[StudentLabSubmission], StudentStats]:
        """
        Расчет статистики по лабам.
        """
        labs_data = []
        stats = StudentStats()
        stats.labs_total = len(labs)
        now = dt.now(timezone.utc)
        
        for lab in labs:
            sub = subs_map.get(lab.id)
            is_overdue = False
            
            if lab.deadline:
                deadline_aware = lab.deadline if lab.deadline.tzinfo else lab.deadline.replace(tzinfo=timezone.utc)
                if not sub and deadline_aware < now:
                    is_overdue = True
                    stats.labs_overdue += 1
            
            if sub:
                stats.labs_submitted += 1
                if sub.status.value == "ACCEPTED":
                    stats.labs_accepted += 1
                    stats.points_earned += sub.grade or 0
                elif sub.status.value == "REJECTED":
                    stats.labs_rejected += 1
                else:
                    stats.labs_pending += 1
            
            stats.points_max += lab.max_grade
            
            labs_data.append(StudentLabSubmission(
                lab_id=lab.id,
                lab_title=lab.title,
                status=sub.status.value if sub else None,
                grade=sub.grade if sub else None,
                max_grade=lab.max_grade,
                deadline=lab.deadline,
                submitted_at=sub.created_at if sub else None,
                feedback=sub.feedback if sub else None,
                is_overdue=is_overdue,
            ))
        
        # Процент баллов
        if stats.points_max > 0:
            stats.points_percent = round((stats.points_earned / stats.points_max) * 100, 1)
            
        return labs_data, stats

