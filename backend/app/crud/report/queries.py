"""Запросы на чтение для публичных отчётов."""
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport

logger = logging.getLogger(__name__)


class ReportQueries:
    """Методы чтения для GroupReport."""

    async def get_by_id(
        self,
        db: AsyncSession,
        report_id: UUID
    ) -> GroupReport | None:
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
    ) -> GroupReport | None:
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
            query = query.where(GroupReport.is_active)

        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if report is None:
            return None

        if check_expiry and report.expires_at and datetime.now(UTC) > report.expires_at:
            logger.info(f"Report {code} has expired")
            return None

        return report

    async def get_by_teacher(
        self,
        db: AsyncSession,
        teacher_id: UUID,
        *,
        include_inactive: bool = False
    ) -> list[GroupReport]:
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
            query = query.where(GroupReport.is_active)

        query = query.order_by(GroupReport.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_group(
        self,
        db: AsyncSession,
        group_id: UUID,
        *,
        include_inactive: bool = False
    ) -> list[GroupReport]:
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
            query = query.where(GroupReport.is_active)

        query = query.order_by(GroupReport.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())
