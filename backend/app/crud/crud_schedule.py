"""CRUD операции для Schedule и Lesson."""
import logging
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.schedule import ScheduleItem, DayOfWeek, LessonType, WeekParity
from app.models.lesson import Lesson

logger = logging.getLogger(__name__)


class CRUDSchedule:
    """CRUD для расписания"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        group_id: UUID,
        day_of_week: DayOfWeek,
        lesson_number: int,
        lesson_type: LessonType,
        start_date: date,
        subject: Optional[str] = None,
        room: Optional[str] = None,
        teacher_id: Optional[UUID] = None,
        end_date: Optional[date] = None,
        week_parity: Optional[WeekParity] = None,
        subgroup: Optional[int] = None
    ) -> ScheduleItem:
        db_obj = ScheduleItem(
            group_id=group_id,
            day_of_week=day_of_week,
            lesson_number=lesson_number,
            lesson_type=lesson_type,
            subject=subject,
            room=room,
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            week_parity=week_parity,
            subgroup=subgroup
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created schedule item: {db_obj.id}")
        return db_obj

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ScheduleItem]:
        result = await db.execute(select(ScheduleItem).where(ScheduleItem.id == id))
        return result.scalar_one_or_none()

    async def get_by_group(
        self,
        db: AsyncSession,
        group_id: UUID,
        active_only: bool = True
    ) -> List[ScheduleItem]:
        query = select(ScheduleItem).where(ScheduleItem.group_id == group_id)
        if active_only:
            query = query.where(ScheduleItem.is_active == True)
        query = query.order_by(ScheduleItem.day_of_week, ScheduleItem.lesson_number)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ScheduleItem,
        **kwargs
    ) -> ScheduleItem:
        for field, value in kwargs.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            logger.info(f"Deleted schedule item: {id}")
            return True
        return False


class CRUDLesson:
    """CRUD для занятий"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        group_id: UUID,
        date: date,
        lesson_number: int,
        lesson_type: LessonType,
        schedule_item_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        work_id: Optional[UUID] = None,
        subgroup: Optional[int] = None
    ) -> Lesson:
        db_obj = Lesson(
            group_id=group_id,
            schedule_item_id=schedule_item_id,
            date=date,
            lesson_number=lesson_number,
            lesson_type=lesson_type,
            topic=topic,
            work_id=work_id,
            subgroup=subgroup
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created lesson: {db_obj.id}")
        return db_obj

    async def get_or_create(
        self,
        db: AsyncSession,
        *,
        group_id: UUID,
        date: date,
        lesson_number: int,
        lesson_type: LessonType,
        schedule_item_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        work_id: Optional[UUID] = None,
        subgroup: Optional[int] = None
    ) -> Optional[Lesson]:
        """Получить существующее занятие или создать новое. Возвращает None если уже существует."""
        existing = await db.execute(
            select(Lesson).where(
                Lesson.group_id == group_id,
                Lesson.date == date,
                Lesson.lesson_number == lesson_number,
                Lesson.subgroup == subgroup
            )
        )
        if existing.scalar_one_or_none():
            return None  # Уже существует
        
        return await self.create(
            db,
            group_id=group_id,
            date=date,
            lesson_number=lesson_number,
            lesson_type=lesson_type,
            schedule_item_id=schedule_item_id,
            topic=topic,
            work_id=work_id,
            subgroup=subgroup
        )

    async def get(self, db: AsyncSession, id: UUID) -> Optional[Lesson]:
        result = await db.execute(select(Lesson).where(Lesson.id == id))
        return result.scalar_one_or_none()

    async def get_by_group_and_period(
        self,
        db: AsyncSession,
        group_id: UUID,
        start_date: date,
        end_date: date,
        lesson_type: Optional[LessonType] = None
    ) -> List[Lesson]:
        query = select(Lesson).where(
            and_(
                Lesson.group_id == group_id,
                Lesson.date >= start_date,
                Lesson.date <= end_date
            )
        )
        if lesson_type:
            query = query.where(Lesson.lesson_type == lesson_type)
        query = query.order_by(Lesson.date, Lesson.lesson_number)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Lesson,
        **kwargs
    ) -> Lesson:
        for field, value in kwargs.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def cancel(
        self,
        db: AsyncSession,
        *,
        db_obj: Lesson,
        reason: Optional[str] = None
    ) -> Lesson:
        db_obj.is_cancelled = True
        db_obj.cancellation_reason = reason
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Cancelled lesson: {db_obj.id}")
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            logger.info(f"Deleted lesson: {id}")
            return True
        return False

    async def get_grouped_lectures(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """
        Получить лекции сгруппированные по (дата + пара + предмет).
        Возвращает список с группами для каждой лекции.
        """
        from sqlalchemy.orm import selectinload
        from app.models.group import Group
        from app.models.subject import Subject
        
        query = (
            select(Lesson)
            .options(selectinload(Lesson.group), selectinload(Lesson.subject))
            .where(
                and_(
                    Lesson.lesson_type == LessonType.LECTURE,
                    Lesson.date >= start_date,
                    Lesson.date <= end_date
                )
            )
            .order_by(Lesson.date, Lesson.lesson_number)
        )
        result = await db.execute(query)
        lessons = list(result.scalars().all())
        
        # Группируем по (date, lesson_number, subject_id)
        grouped: dict = {}
        for lesson in lessons:
            key = (lesson.date, lesson.lesson_number, lesson.subject_id)
            if key not in grouped:
                grouped[key] = {
                    "date": lesson.date.isoformat(),
                    "lesson_number": lesson.lesson_number,
                    "subject_id": str(lesson.subject_id) if lesson.subject_id else None,
                    "subject_name": lesson.subject.name if lesson.subject else None,
                    "topic": lesson.topic,
                    "is_cancelled": lesson.is_cancelled,
                    "ended_early": lesson.ended_early,
                    "groups": []
                }
            grouped[key]["groups"].append({
                "id": str(lesson.group.id),
                "name": lesson.group.name,
                "lesson_id": str(lesson.id)
            })
        
        return list(grouped.values())


schedule = CRUDSchedule()
lesson = CRUDLesson()
