"""Build and apply safe lab grade import plans."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Group, Lab, Lesson, LessonGrade, LessonType, User, UserRole
from app.services.attestation.deadline_validator import get_max_allowed_grade
from app.services.journal_grade_service import journal_grade_service
from app.services.lab_grade_import.types import ImportIssue, ImportPlan, ParsedGradeEntry, PlannedGradeWrite

LAB_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)
DEFAULT_START_DATE = date(2026, 3, 13)


class LabGradeImportPlanner:
    def __init__(self, *, start_date: date = DEFAULT_START_DATE) -> None:
        self.start_date = start_date

    async def build_plan(self, db: AsyncSession, entries: list[ParsedGradeEntry]) -> ImportPlan:
        plan = ImportPlan(parsed=len(entries))
        planned_work_keys: set[tuple[UUID, UUID, int]] = set()
        planned_cell_keys: set[tuple[UUID, UUID]] = set()

        for entry in entries:
            write = await self._plan_entry(db, entry, plan)
            if write is None:
                continue

            work_key = (write.student_id, write.subject_id, entry.work_number)
            if work_key in planned_work_keys:
                plan.issues.append(ImportIssue(entry, "duplicate_source_work", "Дубликат в исходном файле"))
                continue

            cell_key = (write.student_id, write.lesson_id)
            if cell_key in planned_cell_keys:
                plan.issues.append(ImportIssue(entry, "source_cell_conflict", "В плане уже есть оценка на эту пару"))
                continue

            planned_work_keys.add(work_key)
            planned_cell_keys.add(cell_key)
            plan.planned.append(write)

        return plan

    async def apply_plan(self, db: AsyncSession, plan: ImportPlan, actor_id: UUID) -> int:
        applied = 0
        for write in plan.planned:
            lesson = await db.get(Lesson, write.lesson_id)
            if lesson is None:
                raise RuntimeError(f"Lesson disappeared before apply: {write.lesson_id}")
            await journal_grade_service.upsert_grade(
                db=db,
                lesson=lesson,
                student_id=write.student_id,
                grade=write.entry.grade,
                work_number=write.entry.work_number,
                comment=f"Импорт из черновика, строка {write.entry.line_number}",
                actor_id=actor_id,
            )
            applied += 1
        return applied

    async def _plan_entry(
        self, db: AsyncSession, entry: ParsedGradeEntry, plan: ImportPlan
    ) -> PlannedGradeWrite | None:
        if entry.source_date is None:
            plan.issues.append(ImportIssue(entry, "missing_source_date", "Не указана дата"))
            return None

        resolved_student = await self._resolve_student_group(db, entry)
        if resolved_student is None:
            plan.issues.append(ImportIssue(entry, "student_not_found", "Студент не найден или неоднозначен"))
            return None
        student, group = resolved_student

        target = await self._resolve_target_lesson_and_lab(db, group, student, entry.work_number)
        if target is None:
            plan.issues.append(ImportIssue(entry, "lesson_or_lab_not_found", "Не найдена подходящая пара"))
            return None
        lesson, lab = target
        if lesson.subject_id is None:
            plan.issues.append(ImportIssue(entry, "lesson_subject_missing", "У пары не указан предмет"))
            return None

        if await self._has_existing_work_grade(db, student.id, lesson.subject_id, entry.work_number):
            plan.issues.append(ImportIssue(entry, "existing_grade", "Оценка за эту лабораторную уже есть"))
            return None

        if await self._has_other_grade_on_lesson(db, student.id, lesson.id):
            plan.issues.append(ImportIssue(entry, "lesson_cell_taken", "На выбранной паре уже есть другая оценка"))
            return None

        max_allowed = await get_max_allowed_grade(db, lesson, student_id=student.id, work_number=entry.work_number)
        if entry.grade > max_allowed:
            plan.issues.append(ImportIssue(entry, "deadline_limit", f"Максимальная оценка по дедлайну: {max_allowed}"))
            return None

        return PlannedGradeWrite(
            entry=entry,
            student_id=student.id,
            student_name=student.full_name,
            group_id=group.id,
            group_name=group.name,
            subject_id=lesson.subject_id,
            lab_id=lab.id if lab else None,
            lesson_id=lesson.id,
            lesson_date=lesson.date,
            lesson_number=lesson.lesson_number,
        )

    async def _resolve_group(self, db: AsyncSession, label: str) -> Group | None:
        normalized = _normalize_label(label)
        candidates = await _scalars(
            db,
            select(Group).where(or_(func.lower(Group.code) == normalized, func.lower(Group.name) == normalized)),
        )
        if not candidates:
            digits = "".join(ch for ch in label if ch.isdigit())
            if len(digits) >= 3:
                candidates = await _scalars(
                    db,
                    select(Group).where(or_(Group.code.ilike(f"%{digits}%"), Group.name.ilike(f"%{digits}%"))),
                )
        return candidates[0] if len(candidates) == 1 else None

    async def _resolve_student_group(self, db: AsyncSession, entry: ParsedGradeEntry) -> tuple[User, Group] | None:
        label_group = await self._resolve_group(db, entry.group_label) if entry.group_label else None
        candidates = await self._resolve_student_candidates(db, entry.student_label)
        if label_group is not None:
            group_candidates = [(student, group) for student, group in candidates if group.id == label_group.id]
            if len(group_candidates) == 1:
                return group_candidates[0]
            if group_candidates:
                return None
        return candidates[0] if len(candidates) == 1 else None

    async def _resolve_student_candidates(self, db: AsyncSession, label: str) -> list[tuple[User, Group]]:
        surname = label.split()[0]
        if not surname:
            return []

        result = await db.execute(
            select(User, Group)
            .join(Group, User.group_id == Group.id)
            .where(
                User.role == UserRole.STUDENT,
                User.is_active.is_(True),
                User.full_name.ilike(f"{surname[:1]}%"),
                Group.is_archived.is_(False),
            )
        )
        normalized_surname = _normalize_for_match(surname)
        return [
            (student, group)
            for student, group in result.all()
            if _normalize_for_match(student.full_name.split()[0]) == normalized_surname
        ]

    async def _resolve_target_lesson_and_lab(
        self, db: AsyncSession, group: Group, student: User, work_number: int
    ) -> tuple[Lesson, Lab | None] | None:
        lesson = await self._resolve_lesson_by_work_number(db, group, student, work_number)
        if lesson is None:
            lesson = await self._resolve_lesson_by_sequence(db, group, student, work_number)
        if lesson is None:
            return None
        lab = await self._resolve_lab_for_lesson(db, lesson, work_number)
        return lesson, lab

    async def _resolve_lesson_by_work_number(
        self, db: AsyncSession, group: Group, student: User, work_number: int
    ) -> Lesson | None:
        conditions = [
            Lesson.group_id == group.id,
            Lesson.date >= self.start_date,
            Lesson.work_number == work_number,
            Lesson.lesson_type.in_(LAB_LESSON_TYPES),
            Lesson.is_cancelled.is_(False),
        ]
        conditions.extend(_student_lesson_scope(student))

        result = await db.execute(
            select(Lesson)
            .where(and_(*conditions))
            .order_by(Lesson.subject_id, Lesson.date, Lesson.lesson_number, Lesson.subgroup.desc().nullslast())
        )
        rows = list(result.scalars().all())
        subject_ids = {lesson.subject_id for lesson in rows}
        if len(subject_ids) != 1 or not rows:
            return None
        return rows[0]

    async def _resolve_lesson_by_sequence(
        self, db: AsyncSession, group: Group, student: User, work_number: int
    ) -> Lesson | None:
        conditions = [
            Lesson.group_id == group.id,
            Lesson.date >= self.start_date,
            Lesson.lesson_type.in_(LAB_LESSON_TYPES),
            Lesson.is_cancelled.is_(False),
        ]
        conditions.extend(_student_lesson_scope(student))
        result = await db.execute(select(Lesson).where(and_(*conditions)).order_by(Lesson.date, Lesson.lesson_number))
        lessons = list(result.scalars().all())
        if len(lessons) < work_number:
            return None
        return lessons[work_number - 1]

    async def _resolve_lab_for_lesson(self, db: AsyncSession, lesson: Lesson, work_number: int) -> Lab | None:
        if lesson.subject_id is None:
            return None
        result = await db.execute(
            select(Lab)
            .where(Lab.subject_id == lesson.subject_id, Lab.number == work_number, Lab.deleted_at.is_(None))
            .order_by(Lab.is_published.desc(), Lab.created_at.desc(), Lab.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _has_existing_work_grade(
        self, db: AsyncSession, student_id: UUID, subject_id: UUID, work_number: int
    ) -> bool:
        result = await db.execute(
            select(LessonGrade.id)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(
                LessonGrade.student_id == student_id,
                LessonGrade.work_number == work_number,
                Lesson.subject_id == subject_id,
                Lesson.is_cancelled.is_(False),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _has_other_grade_on_lesson(self, db: AsyncSession, student_id: UUID, lesson_id: UUID) -> bool:
        result = await db.execute(
            select(LessonGrade.id)
            .where(LessonGrade.student_id == student_id, LessonGrade.lesson_id == lesson_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


async def _scalars(db: AsyncSession, statement: Any) -> list[Any]:
    result = await db.execute(statement)
    return list(result.scalars().all())


def _normalize_label(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _normalize_for_match(value: str) -> str:
    return _normalize_label(value).replace("ё", "е")


def _student_lesson_scope(student: User) -> list[Any]:
    if student.subgroup is None:
        return [Lesson.subgroup.is_(None)]
    return [or_(Lesson.subgroup == student.subgroup, Lesson.subgroup.is_(None))]
