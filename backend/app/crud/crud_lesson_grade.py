"""
CRUD операции для оценок за занятия.
"""

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lesson_grade import LessonGrade

logger = logging.getLogger(__name__)


async def create_lesson_grade(
    db: AsyncSession,
    lesson_id: UUID,
    student_id: UUID,
    grade: int,
    work_number: int | None = None,
    comment: str | None = None,
    created_by: UUID | None = None,
) -> LessonGrade:
    """Создать оценку за занятие."""
    lesson_grade = LessonGrade(
        lesson_id=lesson_id,
        student_id=student_id,
        grade=grade,
        work_number=work_number,
        comment=comment,
        created_by=created_by,
    )
    db.add(lesson_grade)
    await db.commit()
    await db.refresh(lesson_grade)
    logger.info(f"Created lesson grade: lesson={lesson_id}, student={student_id}, grade={grade}")
    return lesson_grade


async def get_lesson_grade(db: AsyncSession, grade_id: UUID) -> LessonGrade | None:
    """Получить оценку по ID."""
    result = await db.execute(select(LessonGrade).where(LessonGrade.id == grade_id))
    return result.scalar_one_or_none()


async def get_lesson_grades_by_lesson(db: AsyncSession, lesson_id: UUID) -> list[LessonGrade]:
    """Получить все оценки за занятие."""
    result = await db.execute(
        select(LessonGrade).where(LessonGrade.lesson_id == lesson_id).options(selectinload(LessonGrade.student))
    )
    return list(result.scalars().all())


async def get_lesson_grades_by_student(
    db: AsyncSession, student_id: UUID, lesson_ids: list[UUID] | None = None
) -> list[LessonGrade]:
    """Получить оценки студента (опционально по списку занятий)."""
    query = select(LessonGrade).where(LessonGrade.student_id == student_id)
    if lesson_ids:
        query = query.where(LessonGrade.lesson_id.in_(lesson_ids))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_student_lesson_grade(
    db: AsyncSession, lesson_id: UUID, student_id: UUID, work_number: int | None = None
) -> LessonGrade | None:
    """Получить оценку студента за конкретное занятие и работу."""
    conditions = [LessonGrade.lesson_id == lesson_id, LessonGrade.student_id == student_id]
    if work_number is not None:
        conditions.append(LessonGrade.work_number == work_number)
    else:
        conditions.append(LessonGrade.work_number.is_(None))

    result = await db.execute(select(LessonGrade).where(and_(*conditions)))
    return result.scalar_one_or_none()


async def get_student_grade_by_work(
    db: AsyncSession,
    student_id: UUID,
    work_number: int,
    group_id: UUID | None = None,
    subject_id: UUID | None = None,
    exclude_grade_id: UUID | None = None,
) -> LessonGrade | None:
    """
    Получить оценку студента за работу (независимо от занятия).
    Используется для проверки: уже есть оценка за эту лабу?
    """
    from app.models.lesson import Lesson

    query = (
        select(LessonGrade)
        .join(Lesson, LessonGrade.lesson_id == Lesson.id)
        .where(and_(LessonGrade.student_id == student_id, LessonGrade.work_number == work_number))
    )
    if group_id:
        query = query.where(Lesson.group_id == group_id)
    if subject_id is not None:
        query = query.where(Lesson.subject_id == subject_id)
    if exclude_grade_id is not None:
        query = query.where(LessonGrade.id != exclude_grade_id)

    query = query.order_by(LessonGrade.grade.desc(), LessonGrade.updated_at.desc(), LessonGrade.created_at.desc())

    result = await db.execute(query)
    return result.scalars().first()


async def update_lesson_grade(
    db: AsyncSession,
    grade_id: UUID,
    grade: int | None = None,
    work_number: int | None = None,
    comment: str | None = None,
) -> LessonGrade | None:
    """Обновить оценку."""
    result = await db.execute(
        select(LessonGrade).options(selectinload(LessonGrade.lesson)).where(LessonGrade.id == grade_id)
    )
    lesson_grade = result.scalar_one_or_none()
    if not lesson_grade:
        return None

    if work_number is not None and lesson_grade.lesson:
        existing_for_work = await get_student_grade_by_work(
            db,
            lesson_grade.student_id,
            work_number,
            group_id=lesson_grade.lesson.group_id,
            subject_id=lesson_grade.lesson.subject_id,
            exclude_grade_id=lesson_grade.id,
        )
        if existing_for_work and existing_for_work.id != lesson_grade.id:
            existing_for_work.lesson_id = lesson_grade.lesson_id
            existing_for_work.work_number = work_number
            existing_for_work.grade = grade if grade is not None else lesson_grade.grade
            existing_for_work.comment = comment if comment is not None else lesson_grade.comment
            await db.delete(lesson_grade)
            await db.commit()
            await db.refresh(existing_for_work)
            logger.info(
                f"Merged lesson grade on update: source={grade_id}, target={existing_for_work.id}, work={work_number}"
            )
            return existing_for_work

    if grade is not None:
        lesson_grade.grade = grade
    if work_number is not None:
        lesson_grade.work_number = work_number
    if comment is not None:
        lesson_grade.comment = comment

    await db.commit()
    await db.refresh(lesson_grade)
    logger.info(f"Updated lesson grade: {grade_id}")
    return lesson_grade


async def delete_lesson_grade(db: AsyncSession, grade_id: UUID) -> bool:
    """Удалить оценку."""
    lesson_grade = await get_lesson_grade(db, grade_id)
    if not lesson_grade:
        return False

    await db.delete(lesson_grade)
    await db.commit()
    logger.info(f"Deleted lesson grade: {grade_id}")
    return True


async def upsert_lesson_grade(
    db: AsyncSession,
    lesson_id: UUID,
    student_id: UUID,
    grade: int,
    work_number: int | None = None,
    comment: str | None = None,
    created_by: UUID | None = None,
    group_id: UUID | None = None,
    subject_id: UUID | None = None,
) -> LessonGrade:
    """
    Создать или обновить оценку (атомарно через ON CONFLICT).

    Логика:
    1. Если work_number указан — ищем существующую оценку за эту лабу (любое занятие в группе)
    2. Если найдена — обновляем (перемещаем на новое занятие)
    3. Если нет — используем INSERT ON CONFLICT для атомарного upsert
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    # Если work_number указан, сначала проверяем есть ли оценка за эту работу
    # на ДРУГОМ занятии (чтобы переместить её)
    if work_number is not None:
        existing = await get_student_grade_by_work(
            db,
            student_id,
            work_number,
            group_id=group_id,
            subject_id=subject_id,
        )
        if existing and existing.lesson_id != lesson_id:
            existing.grade = grade
            existing.lesson_id = lesson_id
            if comment is not None:
                existing.comment = comment
            await db.flush()
            await db.refresh(existing)
            logger.info(f"Moved lesson grade: student={student_id}, work={work_number}, grade={grade}")
            return existing

    stmt = pg_insert(LessonGrade).values(
        lesson_id=lesson_id,
        student_id=student_id,
        grade=grade,
        work_number=work_number,
        comment=comment,
        created_by=created_by,
    )

    stmt = stmt.on_conflict_do_update(
        constraint="uq_lesson_grade_student_lesson_work",
        set_={
            "grade": stmt.excluded.grade,
            "comment": stmt.excluded.comment,
        },
    )

    await db.execute(stmt)
    await db.flush()

    lesson_grade = await get_student_lesson_grade(db, lesson_id, student_id, work_number)
    logger.info(f"Upserted lesson grade: student={student_id}, work={work_number}, grade={grade}")
    return lesson_grade


async def bulk_upsert_lesson_grades(
    db: AsyncSession,
    lesson_id: UUID,
    grades_data: list[dict],
    created_by: UUID | None = None,
    group_id: UUID | None = None,
    subject_id: UUID | None = None,
) -> list[LessonGrade]:
    """
    Bulk upsert оценок за занятие.
    Один запрос на загрузку существующих + один commit.

    Args:
        grades_data: [{"student_id": UUID, "grade": int, "work_number": int|None, "comment": str|None}, ...]
        group_id: для cross-lesson проверки дубликатов (BUG-4 fix)
    """
    if not grades_data:
        return []

    # Собираем ключи для поиска существующих
    student_ids = [g["student_id"] for g in grades_data]

    # Загружаем все существующие оценки одним запросом
    existing_query = select(LessonGrade).where(
        and_(LessonGrade.lesson_id == lesson_id, LessonGrade.student_id.in_(student_ids))
    )
    result = await db.execute(existing_query)
    existing_grades = list(result.scalars().all())

    # Индексируем: (student_id, work_number) -> grade
    existing_map = {}
    for g in existing_grades:
        key = (g.student_id, g.work_number)
        existing_map[key] = g

    updated = []
    for data in grades_data:
        key = (data["student_id"], data.get("work_number"))
        existing = existing_map.get(key)

        if not existing and data.get("work_number") is not None:
            # BUG-4 fix: проверяем есть ли оценка за эту работу на ДРУГОМ занятии
            existing_other = await get_student_grade_by_work(
                db,
                data["student_id"],
                data["work_number"],
                group_id=group_id,
                subject_id=subject_id,
            )
            if existing_other and existing_other.lesson_id != lesson_id:
                existing = existing_other

        if existing:
            existing.grade = data["grade"]
            existing.lesson_id = lesson_id  # перемещаем на текущее занятие если нужно
            if data.get("comment") is not None:
                existing.comment = data["comment"]
            updated.append(existing)
        else:
            new_grade = LessonGrade(
                lesson_id=lesson_id,
                student_id=data["student_id"],
                grade=data["grade"],
                work_number=data.get("work_number"),
                comment=data.get("comment"),
                created_by=created_by,
            )
            db.add(new_grade)
            updated.append(new_grade)

    await db.flush()

    # Refresh all
    for g in updated:
        await db.refresh(g)

    logger.info(f"Bulk upserted {len(updated)} grades for lesson {lesson_id}")
    return updated
