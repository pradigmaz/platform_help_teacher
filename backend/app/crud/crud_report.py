"""CRUD операции для публичных отчётов."""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport, ReportType
from app.models.report_view import ReportView
from app.services.reports.security import generate_code, hash_pin

logger = logging.getLogger(__name__)


class CRUDReport:
    """CRUD операции для GroupReport."""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        group_id: UUID,
        created_by: UUID,
        report_type: ReportType = ReportType.FULL,
        expires_in_days: Optional[int] = None,
        pin_code: Optional[str] = None,
        show_names: bool = True,
        show_grades: bool = True,
        show_attendance: bool = True,
        show_notes: bool = True,
        show_rating: bool = True,
    ) -> GroupReport:
        """
        Создать новый публичный отчёт.
        
        Args:
            db: Сессия БД
            group_id: ID группы
            created_by: ID преподавателя
            report_type: Тип отчёта
            expires_in_days: Срок действия в днях (None = бессрочно)
            pin_code: PIN-код для защиты (None = без защиты)
            show_*: Настройки видимости
        
        Returns:
            Созданный отчёт
        """
        code = await self._generate_unique_code(db)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        pin_hash = None
        if pin_code:
            pin_hash = hash_pin(pin_code)
        
        report = GroupReport(
            group_id=group_id,
            created_by=created_by,
            code=code,
            report_type=report_type.value if isinstance(report_type, ReportType) else report_type,
            expires_at=expires_at,
            pin_hash=pin_hash,
            show_names=show_names,
            show_grades=show_grades,
            show_attendance=show_attendance,
            show_notes=show_notes,
            show_rating=show_rating,
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"Created report {code} for group {group_id}")
        return report

    async def get_by_id(
        self,
        db: AsyncSession,
        report_id: UUID
    ) -> Optional[GroupReport]:
        """
        Получить отчёт по ID.
        
        Args:
            db: Сессия БД
            report_id: ID отчёта
        
        Returns:
            Отчёт или None
        """
        result = await db.execute(
            select(GroupReport).where(GroupReport.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(
        self,
        db: AsyncSession,
        code: str,
        *,
        check_active: bool = True,
        check_expiry: bool = True
    ) -> Optional[GroupReport]:
        """
        Получить отчёт по уникальному коду.
        
        Args:
            db: Сессия БД
            code: 8-символьный код отчёта
            check_active: Проверять активность
            check_expiry: Проверять срок действия
        
        Returns:
            Отчёт или None (если не найден/неактивен/истёк)
        """
        query = select(GroupReport).where(GroupReport.code == code)
        
        if check_active:
            query = query.where(GroupReport.is_active == True)
        
        result = await db.execute(query)
        report = result.scalar_one_or_none()
        
        if report is None:
            return None
        
        if check_expiry and report.expires_at:
            if datetime.now(timezone.utc) > report.expires_at:
                logger.info(f"Report {code} has expired")
                return None
        
        return report
    
    async def get_by_teacher(
        self,
        db: AsyncSession,
        teacher_id: UUID,
        *,
        include_inactive: bool = False
    ) -> List[GroupReport]:
        """
        Получить все отчёты преподавателя.
        
        Args:
            db: Сессия БД
            teacher_id: ID преподавателя
            include_inactive: Включать деактивированные
        
        Returns:
            Список отчётов
        """
        query = select(GroupReport).where(GroupReport.created_by == teacher_id)
        
        if not include_inactive:
            query = query.where(GroupReport.is_active == True)
        
        query = query.order_by(GroupReport.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_group(
        self,
        db: AsyncSession,
        group_id: UUID,
        *,
        include_inactive: bool = False
    ) -> List[GroupReport]:
        """
        Получить все отчёты для группы.
        
        Args:
            db: Сессия БД
            group_id: ID группы
            include_inactive: Включать деактивированные
        
        Returns:
            Список отчётов
        """
        query = select(GroupReport).where(GroupReport.group_id == group_id)
        
        if not include_inactive:
            query = query.where(GroupReport.is_active == True)
        
        query = query.order_by(GroupReport.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        report: GroupReport,
        *,
        expires_in_days: Optional[int] = None,
        pin_code: Optional[str] = None,
        remove_pin: bool = False,
        show_names: Optional[bool] = None,
        show_grades: Optional[bool] = None,
        show_attendance: Optional[bool] = None,
        show_notes: Optional[bool] = None,
        show_rating: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> GroupReport:
        """
        Обновить настройки отчёта.
        
        Args:
            db: Сессия БД
            report: Отчёт для обновления
            expires_in_days: Новый срок действия
            pin_code: Новый PIN-код
            remove_pin: Удалить PIN-защиту
            show_*: Настройки видимости
            is_active: Статус активности
        
        Returns:
            Обновлённый отчёт
        """
        # PIN handling
        if remove_pin:
            report.pin_hash = None
        elif pin_code:
            report.pin_hash = hash_pin(pin_code)
        
        # Expiration
        if expires_in_days is not None:
            if expires_in_days > 0:
                report.expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            else:
                report.expires_at = None  # Бессрочно
        
        # Visibility settings
        if show_names is not None:
            report.show_names = show_names
        if show_grades is not None:
            report.show_grades = show_grades
        if show_attendance is not None:
            report.show_attendance = show_attendance
        if show_notes is not None:
            report.show_notes = show_notes
        if show_rating is not None:
            report.show_rating = show_rating
        
        # Status
        if is_active is not None:
            report.is_active = is_active
        
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"Updated report {report.code}")
        return report
    
    async def deactivate(
        self,
        db: AsyncSession,
        report: GroupReport
    ) -> GroupReport:
        """
        Деактивировать отчёт.
        
        Args:
            db: Сессия БД
            report: Отчёт для деактивации
        
        Returns:
            Деактивированный отчёт
        """
        report.is_active = False
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"Deactivated report {report.code}")
        return report
    
    async def regenerate_code(
        self,
        db: AsyncSession,
        report: GroupReport
    ) -> GroupReport:
        """
        Сгенерировать новый код для отчёта.
        Старый код становится недействительным.
        
        Args:
            db: Сессия БД
            report: Отчёт
        
        Returns:
            Отчёт с новым кодом
        """
        old_code = report.code
        report.code = await self._generate_unique_code(db)
        
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"Regenerated code: {old_code} -> {report.code}")
        return report
    
    async def delete(
        self,
        db: AsyncSession,
        report: GroupReport
    ) -> bool:
        """
        Удалить отчёт (физическое удаление).
        
        Args:
            db: Сессия БД
            report: Отчёт для удаления
        
        Returns:
            True если удалён
        """
        await db.delete(report)
        await db.commit()
        logger.info(f"Deleted report {report.code}")
        return True

    async def increment_views(
        self,
        db: AsyncSession,
        report: GroupReport
    ) -> GroupReport:
        """
        Увеличить счётчик просмотров.
        
        Args:
            db: Сессия БД
            report: Отчёт
        
        Returns:
            Обновлённый отчёт
        """
        report.views_count += 1
        report.last_viewed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(report)
        return report
    
    async def _generate_unique_code(self, db: AsyncSession) -> str:
        """
        Генерация уникального 8-символьного кода.
        
        Args:
            db: Сессия БД
        
        Returns:
            Уникальный код
        
        Raises:
            RuntimeError: Если не удалось сгенерировать уникальный код
        """
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_code()
            existing = await db.execute(
                select(GroupReport.id).where(GroupReport.code == code)
            )
            if existing.scalar_one_or_none() is None:
                return code
        
        raise RuntimeError("Failed to generate unique code after max attempts")


# Singleton instance
crud_report = CRUDReport()
