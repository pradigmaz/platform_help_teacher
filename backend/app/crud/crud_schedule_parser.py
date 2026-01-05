"""
CRUD для автопарсера расписания
"""
from uuid import UUID
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule_parser_config import ScheduleParserConfig
from app.models.schedule_conflict import ScheduleConflict, ConflictType
from app.models.lesson import Lesson
from app.schemas.schedule_parser import ParserConfigCreate, ParserConfigUpdate


async def get_parser_config(db: AsyncSession, teacher_id: UUID) -> Optional[ScheduleParserConfig]:
    """Получить настройки парсера для преподавателя"""
    result = await db.execute(
        select(ScheduleParserConfig).where(ScheduleParserConfig.teacher_id == teacher_id)
    )
    return result.scalar_one_or_none()


async def create_parser_config(
    db: AsyncSession, teacher_id: UUID, data: ParserConfigCreate
) -> ScheduleParserConfig:
    """Создать настройки парсера"""
    config = ScheduleParserConfig(
        teacher_id=teacher_id,
        teacher_name=data.teacher_name,
        enabled=data.enabled,
        day_of_week=data.day_of_week,
        run_time=data.run_time,
        parse_days_ahead=data.parse_days_ahead
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def update_parser_config(
    db: AsyncSession, config: ScheduleParserConfig, data: ParserConfigUpdate
) -> ScheduleParserConfig:
    """Обновить настройки парсера"""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    await db.commit()
    await db.refresh(config)
    return config


async def get_all_enabled_configs(db: AsyncSession) -> list[ScheduleParserConfig]:
    """Получить все включённые конфиги (для Celery)"""
    result = await db.execute(
        select(ScheduleParserConfig).where(ScheduleParserConfig.enabled == True)
    )
    return list(result.scalars().all())


# === Conflicts ===

async def get_unresolved_conflicts(db: AsyncSession, teacher_id: UUID) -> list[ScheduleConflict]:
    """Получить неразрешённые конфликты для преподавателя"""
    # Получаем конфликты через lessons -> groups -> teacher assignments
    result = await db.execute(
        select(ScheduleConflict)
        .where(ScheduleConflict.resolved == False)
        .order_by(ScheduleConflict.created_at.desc())
    )
    return list(result.scalars().all())


async def create_conflict(
    db: AsyncSession,
    lesson_id: UUID,
    conflict_type: ConflictType,
    old_data: dict,
    new_data: Optional[dict] = None
) -> ScheduleConflict:
    """Создать конфликт"""
    conflict = ScheduleConflict(
        lesson_id=lesson_id,
        conflict_type=conflict_type,
        old_data=old_data,
        new_data=new_data
    )
    db.add(conflict)
    await db.commit()
    await db.refresh(conflict)
    return conflict


async def resolve_conflict(
    db: AsyncSession, conflict_id: UUID, action: str
) -> Optional[ScheduleConflict]:
    """Разрешить конфликт"""
    result = await db.execute(
        select(ScheduleConflict).where(ScheduleConflict.id == conflict_id)
    )
    conflict = result.scalar_one_or_none()
    if not conflict:
        return None
    
    conflict.resolved = True
    conflict.resolution = action
    
    # Если accept - применяем изменения
    if action == "accept":
        lesson_result = await db.execute(
            select(Lesson).where(Lesson.id == conflict.lesson_id)
        )
        lesson = lesson_result.scalar_one_or_none()
        if lesson:
            if conflict.conflict_type == ConflictType.DELETED:
                lesson.is_cancelled = True
            elif conflict.conflict_type == ConflictType.CHANGED and conflict.new_data:
                if "topic" in conflict.new_data:
                    lesson.topic = conflict.new_data["topic"]
                if "lesson_type" in conflict.new_data:
                    from app.models.schedule import LessonType
                    lesson.lesson_type = LessonType(conflict.new_data["lesson_type"])
    
    await db.commit()
    await db.refresh(conflict)
    return conflict


async def resolve_all_conflicts(db: AsyncSession, action: str) -> int:
    """Разрешить все конфликты"""
    result = await db.execute(
        select(ScheduleConflict).where(ScheduleConflict.resolved == False)
    )
    conflicts = list(result.scalars().all())
    
    for conflict in conflicts:
        await resolve_conflict(db, conflict.id, action)
    
    return len(conflicts)
