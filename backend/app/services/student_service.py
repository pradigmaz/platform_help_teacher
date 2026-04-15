from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Group, Lab, Lesson, LessonGrade, Submission, SubmissionStatus, User
from app.schemas.student import StudentLabSubmission, StudentProfileOut, StudentStats
from app.services.attestation.lab_progress import dedupe_lesson_grade_rows
from app.services.lab_progress_read_model import normalize_lab_progress


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, student_id: UUID, include_labs: bool = True) -> StudentProfileOut | None:
        """
        Получить профиль студента с его лабораторными работами и статистикой.
        """
        student = await self._get_student(student_id)
        if not student:
            return None

        group_name, ranking_scores = await self._get_group_ranking(student, student_id)
        labs = await self._get_labs(include_details=include_labs)

        # Получаем сдачи студента из submissions
        subs_result = await self.db.execute(select(Submission).where(Submission.user_id == student_id))
        submissions = subs_result.scalars().all()
        subs_map: dict[UUID, Submission] = {sub.lab_id: sub for sub in submissions}

        # Получаем оценки из lesson_grades (журнал)
        grades_map = await self._get_lesson_grades_map(student_id)

        # Собираем данные по лабам и статистику
        labs_data, stats = self._calculate_stats(labs, subs_map, grades_map, include_details=include_labs)
        self._apply_group_ranking(stats, ranking_scores, student_id)

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

    async def get_labs(self, student_id: UUID) -> list[StudentLabSubmission] | None:
        student = await self._get_student(student_id)
        if not student:
            return None

        labs = await self._get_labs(include_details=True)
        subs_result = await self.db.execute(select(Submission).where(Submission.user_id == student_id))
        submissions = subs_result.scalars().all()
        subs_map: dict[UUID, Submission] = {sub.lab_id: sub for sub in submissions}
        grades_map = await self._get_lesson_grades_map(student_id)
        labs_data, _ = self._calculate_stats(labs, subs_map, grades_map, include_details=True)
        return labs_data

    async def _get_student(self, student_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == student_id))
        return result.scalar_one_or_none()

    async def _get_group_ranking(self, student: User, student_id: UUID) -> tuple[str | None, list[tuple[UUID, int]]]:
        if not student.group_id:
            return None, []

        group_result = await self.db.execute(select(Group.name).where(Group.id == student.group_id))
        group_name = group_result.scalar_one_or_none()

        scores_query = (
            select(User.id, func.coalesce(func.sum(Submission.grade), 0))
            .select_from(User)
            .outerjoin(
                Submission,
                (Submission.user_id == User.id) & (Submission.status == SubmissionStatus.ACCEPTED),
            )
            .where(
                User.group_id == student.group_id,
                User.role == "student",
                User.is_active.is_(True),
            )
            .group_by(User.id)
        )
        scores_result = await self.db.execute(scores_query)
        student_scores = [(uid, int(total or 0)) for uid, total in scores_result.all()]
        student_scores.sort(key=lambda item: item[1], reverse=True)

        if student_id not in {uid for uid, _ in student_scores}:
            return group_name, []

        return group_name, student_scores

    async def _get_labs(self, include_details: bool) -> list[Any]:
        if include_details:
            labs_result = await self.db.execute(select(Lab).order_by(Lab.created_at.desc()))
            return list(labs_result.scalars().all())

        labs_result = await self.db.execute(
            select(
                Lab.id,
                Lab.title,
                Lab.subject_id,
                Lab.number,
                Lab.max_grade,
                Lab.deadline_5_lessons,
                Lab.deadline_4_lessons,
            ).order_by(Lab.created_at.desc())
        )
        return list(labs_result.all())

    async def _get_lesson_grades_map(self, student_id: UUID) -> dict[tuple[UUID | None, int], LessonGrade]:
        """
        Получить оценки из журнала (lesson_grades) для студента.
        Возвращает dict: (subject_id, work_number) -> LessonGrade (лучшая оценка)
        """
        grades_result = await self.db.execute(
            select(LessonGrade, Lesson.subject_id)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id == student_id)
            .where(LessonGrade.work_number.isnot(None))
            .where(Lesson.is_cancelled.is_(False))
        )
        rows = grades_result.all()
        grades = dedupe_lesson_grade_rows(rows)
        subject_by_grade_id = {grade.id: subject_id for grade, subject_id in rows}

        grades_map: dict[tuple[UUID | None, int], LessonGrade] = {}
        for grade in grades:
            work_num = grade.work_number
            if work_num is None:
                continue
            subject_id = subject_by_grade_id.get(grade.id)
            grades_map[(subject_id, work_num)] = grade

        return grades_map

    def _calculate_stats(
        self,
        labs: list[Lab],
        subs_map: dict,
        grades_map: dict[tuple[UUID | None, int], LessonGrade],
        include_details: bool,
    ) -> tuple[list[StudentLabSubmission], StudentStats]:
        """
        Расчет статистики по лабам.
        """
        labs_data: list[StudentLabSubmission] = []
        stats = StudentStats()
        stats.labs_total = len(labs)

        for lab in labs:
            lab_id = lab.id
            lab_title = getattr(lab, "title", "")
            lab_subject_id = lab.subject_id
            lab_number = lab.number
            max_grade = lab.max_grade
            deadline_5_lessons = getattr(lab, "deadline_5_lessons", None)
            deadline_4_lessons = getattr(lab, "deadline_4_lessons", None)

            sub = subs_map.get(lab_id)
            journal_grade = grades_map.get((lab_subject_id, lab_number))

            # TODO: is_overdue теперь зависит от количества пар, не от даты
            # Для корректного расчёта нужен доступ к расписанию
            is_overdue = False

            progress = normalize_lab_progress(sub, journal_grade)
            status = sub.status.value if sub else None
            normalized_status = progress.normalized_status
            grade = progress.grade
            submitted_at = progress.submitted_at
            feedback = progress.feedback

            if normalized_status:
                stats.labs_submitted += 1
                if normalized_status == SubmissionStatus.ACCEPTED.value:
                    stats.labs_accepted += 1
                    stats.points_earned += grade or 0
                elif normalized_status == SubmissionStatus.REJECTED.value:
                    stats.labs_rejected += 1
                elif normalized_status == SubmissionStatus.READY.value:
                    stats.labs_pending += 1

            stats.points_max += max_grade

            if include_details:
                labs_data.append(
                    StudentLabSubmission(
                        lab_id=lab_id,
                        lab_title=lab_title,
                        status=status,
                        normalized_status=normalized_status,
                        grade=grade,
                        max_grade=max_grade,
                        deadline_5_lessons=deadline_5_lessons,
                        deadline_4_lessons=deadline_4_lessons,
                        submitted_at=submitted_at,
                        feedback=feedback,
                        is_overdue=is_overdue,
                    )
                )

        # Процент баллов
        if stats.points_max > 0:
            stats.points_percent = round((stats.points_earned / stats.points_max) * 100, 1)

        return labs_data, stats

    def _apply_group_ranking(
        self, stats: StudentStats, student_scores: list[tuple[UUID, int]], student_id: UUID
    ) -> None:
        if not student_scores:
            return

        stats.group_total = len(student_scores)

        current_student_points = next((points for sid, points in student_scores if sid == student_id), None)
        if current_student_points is None:
            return

        stats.group_rank = sum(1 for _, points in student_scores if points > current_student_points) + 1
        if stats.group_rank and stats.group_total > 1:
            stats.group_percentile = round(
                ((stats.group_total - stats.group_rank) / (stats.group_total - 1)) * 100,
                1,
            )
