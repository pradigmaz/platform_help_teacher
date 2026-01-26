"""
Сервис расчёта видимости лаб и дедлайнов по расписанию.

Правила:
- Видимость лабы = MIN(date) занятий с work_number = N для группы/подгруппы
- Активация дедлайна = MAX(date) занятий с work_number = N
- Дедлайн на 5/4 = N уникальных work_number после активации (не занятий!)
- Продления (LabDeadlineExtension) добавляют bonus_lessons к дедлайнам
"""
import logging
from datetime import date, datetime
from typing import Optional, List, Dict
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.lab_deadline_extension import LabDeadlineExtension
from app.services.schedule_constants import MSK_TZ, today_msk, now_msk

logger = logging.getLogger(__name__)


@dataclass
class LabVisibilityInfo:
    """Информация о видимости и дедлайнах лабы для студента."""
    lab_number: int
    is_visible: bool
    visible_from: Optional[date] = None
    deadline_active_from: Optional[date] = None
    lessons_since_activation: int = 0
    deadline_5_status: Optional[str] = None  # 'active', 'expired', None
    deadline_4_status: Optional[str] = None
    lessons_until_deadline_5: Optional[int] = None
    lessons_until_deadline_4: Optional[int] = None
    current_max_grade: int = 5  # Текущий максимальный балл с учётом дедлайна
    has_extension: bool = False  # Есть ли активное продление
    extension_bonus: int = 0  # Сколько бонусных пар от продления


class LabVisibilityService:
    """Сервис расчёта видимости лаб по расписанию."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._subgroup_filter_cache: Optional[list] = None
    
    def _build_subgroup_filter(self, subgroup: Optional[int]) -> list:
        """
        Построить фильтр по подгруппе.
        
        Логика:
        - Занятия для всей группы (subgroup = NULL) видны всем
        - Занятия для конкретной подгруппы видны только студентам этой подгруппы
        - Студент без подгруппы видит ВСЕ занятия (и общие, и по подгруппам)
        """
        if subgroup is not None:
            return [(Lesson.subgroup == None) | (Lesson.subgroup == subgroup)]
        return []  # Студент без подгруппы видит всё
    
    async def get_batch_visibility_info(
        self,
        lab_numbers: List[int],
        group_id: UUID,
        subgroup: Optional[int],
        labs_deadlines: Dict[int, tuple],  # {lab_number: (deadline_5, deadline_4)}
        labs_subjects: Optional[Dict[int, Optional[UUID]]] = None,  # {lab_number: subject_id}
        labs_ids: Optional[Dict[int, UUID]] = None  # {lab_number: lab_id} для проверки продлений
    ) -> Dict[int, LabVisibilityInfo]:
        """
        Batch-загрузка информации о видимости для нескольких лаб.
        Решает проблему N+1 запросов.
        
        labs_subjects: словарь {lab_number: subject_id} для фильтрации по предметам.
        labs_ids: словарь {lab_number: lab_id} для проверки продлений дедлайнов.
        """
        if not lab_numbers:
            return {}
        
        today = today_msk()
        now = now_msk()
        labs_subjects = labs_subjects or {}
        labs_ids = labs_ids or {}
        
        # Загружаем активные продления для группы
        extensions_map: Dict[UUID, int] = {}  # {lab_id: bonus_lessons}
        if labs_ids:
            lab_id_list = list(labs_ids.values())
            ext_query = select(LabDeadlineExtension).where(and_(
                LabDeadlineExtension.lab_id.in_(lab_id_list),
                LabDeadlineExtension.group_id == group_id,
                LabDeadlineExtension.is_active == True,
                # Проверяем expires_at: либо NULL, либо ещё не истекло
                (LabDeadlineExtension.expires_at == None) | (LabDeadlineExtension.expires_at > now)
            ))
            ext_result = await self.db.execute(ext_query)
            for ext in ext_result.scalars().all():
                extensions_map[ext.lab_id] = ext.bonus_lessons
        
        # Группируем лабы по subject_id для оптимизации запросов
        by_subject: Dict[Optional[UUID], List[int]] = {}
        for lab_number in lab_numbers:
            subject_id = labs_subjects.get(lab_number)
            if subject_id not in by_subject:
                by_subject[subject_id] = []
            by_subject[subject_id].append(lab_number)
        
        result: Dict[int, LabVisibilityInfo] = {}
        
        # Обрабатываем каждую группу предметов отдельно
        for subject_id, subject_lab_numbers in by_subject.items():
            subject_result = await self._get_visibility_for_subject(
                lab_numbers=subject_lab_numbers,
                group_id=group_id,
                subgroup=subgroup,
                labs_deadlines=labs_deadlines,
                subject_id=subject_id,
                today=today,
                labs_ids=labs_ids,
                extensions_map=extensions_map
            )
            result.update(subject_result)
        
        return result
    
    async def _get_visibility_for_subject(
        self,
        lab_numbers: List[int],
        group_id: UUID,
        subgroup: Optional[int],
        labs_deadlines: Dict[int, tuple],
        subject_id: Optional[UUID],
        today: date,
        labs_ids: Optional[Dict[int, UUID]] = None,
        extensions_map: Optional[Dict[UUID, int]] = None
    ) -> Dict[int, LabVisibilityInfo]:
        """Получить visibility для лаб одного предмета."""
        labs_ids = labs_ids or {}
        extensions_map = extensions_map or {}
        
        # Базовый фильтр
        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled == False,
        ]
        base_filter.extend(self._build_subgroup_filter(subgroup))
        if subject_id:
            base_filter.append(Lesson.subject_id == subject_id)
        
        # 1. Получаем MIN/MAX даты для всех лаб одним запросом
        dates_query = select(
            Lesson.work_number,
            func.min(Lesson.date).label('min_date'),
            func.max(Lesson.date).label('max_date')
        ).where(
            and_(*base_filter, Lesson.work_number.in_(lab_numbers))
        ).group_by(Lesson.work_number)
        
        dates_result = await self.db.execute(dates_query)
        lab_dates = {row.work_number: (row.min_date, row.max_date) for row in dates_result.all()}
        
        # 2. Получаем все уникальные work_number с датами для подсчёта дедлайнов
        all_labs_query = select(
            Lesson.work_number,
            func.min(Lesson.date).label('first_date')
        ).where(
            and_(*base_filter, Lesson.work_number != None, Lesson.date <= today)
        ).group_by(Lesson.work_number).order_by(func.min(Lesson.date))
        
        all_labs_result = await self.db.execute(all_labs_query)
        all_labs_ordered = [(row.work_number, row.first_date) for row in all_labs_result.all()]
        
        # 3. Строим результат для каждой лабы
        result = {}
        for lab_number in lab_numbers:
            dates = lab_dates.get(lab_number)
            if not dates or not dates[0]:
                result[lab_number] = LabVisibilityInfo(lab_number=lab_number, is_visible=False)
                continue
            
            visible_from, deadline_active_from = dates
            is_visible = visible_from <= today
            
            if not is_visible:
                result[lab_number] = LabVisibilityInfo(
                    lab_number=lab_number,
                    is_visible=False,
                    visible_from=visible_from,
                    deadline_active_from=deadline_active_from
                )
                continue
            
            # Считаем уникальные лабы после первого занятия этой лабы (не занятия!)
            # Дедлайн отсчитывается от visible_from (первое занятие), а не от deadline_active_from
            labs_after = sum(
                1 for wn, first_date in all_labs_ordered
                if first_date > visible_from and wn != lab_number
            )
            
            # Статус дедлайнов
            deadline_5, deadline_4 = labs_deadlines.get(lab_number, (None, None))
            deadline_5_status = None
            deadline_4_status = None
            lessons_until_5 = None
            lessons_until_4 = None
            current_max_grade = 5  # По умолчанию максимум
            
            # Проверяем продление для этой лабы
            lab_id = labs_ids.get(lab_number)
            extension_bonus = extensions_map.get(lab_id, 0) if lab_id else 0
            has_extension = extension_bonus > 0
            
            # Применяем бонус к дедлайнам
            effective_deadline_5 = (deadline_5 + extension_bonus) if deadline_5 is not None else None
            effective_deadline_4 = (deadline_4 + extension_bonus) if deadline_4 is not None else None
            
            if effective_deadline_5 is not None:
                if labs_after >= effective_deadline_5:
                    deadline_5_status = 'expired'
                    current_max_grade = 4  # Дедлайн на 5 истёк
                elif visible_from <= today:
                    deadline_5_status = 'active'
                    lessons_until_5 = effective_deadline_5 - labs_after
                
                logger.debug(
                    f"Lab {lab_number}: labs_after={labs_after}, deadline_5={effective_deadline_5}, "
                    f"status={deadline_5_status}, visible_from={visible_from}"
                )
            
            if effective_deadline_4 is not None:
                if labs_after >= effective_deadline_4:
                    deadline_4_status = 'expired'
                    current_max_grade = 3  # Дедлайн на 4 тоже истёк
                elif visible_from <= today:
                    deadline_4_status = 'active'
                    lessons_until_4 = effective_deadline_4 - labs_after
            
            result[lab_number] = LabVisibilityInfo(
                lab_number=lab_number,
                is_visible=True,
                visible_from=visible_from,
                deadline_active_from=deadline_active_from,
                lessons_since_activation=labs_after,
                deadline_5_status=deadline_5_status,
                deadline_4_status=deadline_4_status,
                lessons_until_deadline_5=lessons_until_5,
                lessons_until_deadline_4=lessons_until_4,
                current_max_grade=current_max_grade,
                has_extension=has_extension,
                extension_bonus=extension_bonus
            )
        
        return result
    
    async def get_visibility_info(
        self,
        lab_number: int,
        group_id: UUID,
        subgroup: Optional[int],
        deadline_5_lessons: Optional[int],
        deadline_4_lessons: Optional[int],
        subject_id: Optional[UUID] = None
    ) -> LabVisibilityInfo:
        """
        Получить информацию о видимости и дедлайнах одной лабы.
        Для batch-операций используйте get_batch_visibility_info.
        """
        result = await self.get_batch_visibility_info(
            lab_numbers=[lab_number],
            group_id=group_id,
            subgroup=subgroup,
            labs_deadlines={lab_number: (deadline_5_lessons, deadline_4_lessons)},
            labs_subjects={lab_number: subject_id}
        )
        return result.get(lab_number, LabVisibilityInfo(lab_number=lab_number, is_visible=False))
    
    async def get_visible_lab_numbers_by_subject(
        self,
        group_id: UUID,
        subgroup: Optional[int],
    ) -> Dict[Optional[UUID], List[int]]:
        """
        Получить словарь {subject_id: [work_numbers]} видимых лаб.
        Для корректной фильтрации лаб по предметам.
        """
        today = today_msk()
        
        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled == False,
            Lesson.work_number != None,
            Lesson.date <= today
        ]
        base_filter.extend(self._build_subgroup_filter(subgroup))
        
        query = select(
            Lesson.subject_id,
            Lesson.work_number
        ).where(and_(*base_filter)).distinct()
        
        result = await self.db.execute(query)
        
        # Группируем по subject_id
        by_subject: Dict[Optional[UUID], List[int]] = {}
        for row in result.all():
            subject_id = row.subject_id
            work_number = row.work_number
            if subject_id not in by_subject:
                by_subject[subject_id] = []
            if work_number not in by_subject[subject_id]:
                by_subject[subject_id].append(work_number)
        
        return by_subject
    
    async def get_visible_lab_numbers(
        self,
        group_id: UUID,
        subgroup: Optional[int],
        subject_id: Optional[UUID] = None
    ) -> List[int]:
        """
        Получить список номеров лаб, видимых студенту на сегодня.
        Если subject_id указан — только для этого предмета.
        """
        today = today_msk()
        
        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled == False,
            Lesson.work_number != None,
            Lesson.date <= today
        ]
        base_filter.extend(self._build_subgroup_filter(subgroup))
        if subject_id:
            base_filter.append(Lesson.subject_id == subject_id)
        
        query = select(Lesson.work_number).where(and_(*base_filter)).distinct()
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]


    async def is_lab_session_now(
        self,
        group_id: UUID,
        subgroup: Optional[int],
        subject_id: Optional[UUID] = None
    ) -> bool:
        """
        Проверить идёт ли сейчас лабораторное занятие для студента.
        
        Условия:
        - Сегодняшняя дата
        - Текущее время попадает в интервал пары
        - Тип занятия = LAB
        - Группа и подгруппа совпадают
        - Занятие не отменено
        """
        from datetime import datetime
        from app.services.schedule_constants import TIME_TO_LESSON_NUMBER, MSK_TZ
        
        now = datetime.now(MSK_TZ)
        today = now.date()
        current_time = now.time()
        
        # Определяем номер текущей пары по времени
        current_lesson_number = None
        for time_range, lesson_num in TIME_TO_LESSON_NUMBER.items():
            start_str, end_str = time_range.split('-')
            start_h, start_m = map(int, start_str.split(':'))
            end_h, end_m = map(int, end_str.split(':'))
            
            from datetime import time as dt_time
            start_time = dt_time(start_h, start_m)
            end_time = dt_time(end_h, end_m)
            
            if start_time <= current_time <= end_time:
                current_lesson_number = lesson_num
                break
        
        if current_lesson_number is None:
            # Сейчас не время пары (перемена или вне учебного времени)
            return False
        
        # Ищем занятие
        filters = [
            Lesson.group_id == group_id,
            Lesson.date == today,
            Lesson.lesson_number == current_lesson_number,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled == False,
        ]
        
        # Фильтр по подгруппе
        if subgroup is not None:
            filters.append((Lesson.subgroup == None) | (Lesson.subgroup == subgroup))
        
        # Фильтр по предмету (если указан)
        if subject_id:
            filters.append(Lesson.subject_id == subject_id)
        
        query = select(Lesson.id).where(and_(*filters)).limit(1)
        result = await self.db.execute(query)
        
        return result.scalar_one_or_none() is not None
