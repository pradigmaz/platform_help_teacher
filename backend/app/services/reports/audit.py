"""
Модуль аудита для публичных отчётов.

Логирование просмотров и статистика.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport
from app.models.report_view import ReportView
from app.schemas.report import ReportViewStats, ReportViewRecord

logger = logging.getLogger(__name__)


class ReportAuditService:
    """Сервис аудита просмотров отчётов."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_view(
        self,
        report_id: UUID,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> ReportView:
        """
        Логирование просмотра отчёта.
        
        Args:
            report_id: ID отчёта
            ip_address: IP адрес клиента
            user_agent: User-Agent браузера
            
        Returns:
            ReportView: Созданная запись
        """
        view = ReportView(
            report_id=report_id,
            ip_address=ip_address,
            user_agent=user_agent[:512] if user_agent else None
        )
        self.db.add(view)
        
        # Обновляем счётчик и время последнего просмотра
        query = select(GroupReport).where(GroupReport.id == report_id)
        result = await self.db.execute(query)
        report = result.scalar_one_or_none()
        
        if report:
            report.views_count += 1
            report.last_viewed_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(view)
        
        logger.debug(f"Logged view for report {report_id} from {ip_address}")
        return view
    
    async def get_view_stats(self, report_id: UUID) -> ReportViewStats:
        """
        Получение статистики просмотров отчёта.
        
        Args:
            report_id: ID отчёта
            
        Returns:
            ReportViewStats: Статистика просмотров
        """
        # Общее количество просмотров
        total_query = select(func.count(ReportView.id)).where(
            ReportView.report_id == report_id
        )
        total_result = await self.db.execute(total_query)
        total_views = total_result.scalar() or 0
        
        # Уникальные IP
        unique_ips_query = select(func.count(func.distinct(ReportView.ip_address))).where(
            ReportView.report_id == report_id
        )
        unique_ips_result = await self.db.execute(unique_ips_query)
        unique_ips = unique_ips_result.scalar() or 0
        
        # Последний просмотр
        last_view_query = select(func.max(ReportView.viewed_at)).where(
            ReportView.report_id == report_id
        )
        last_view_result = await self.db.execute(last_view_query)
        last_viewed_at = last_view_result.scalar()
        
        # Просмотры по датам (последние 30 дней)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        views_by_date_query = (
            select(
                func.date(ReportView.viewed_at).label('date'),
                func.count(ReportView.id).label('count')
            )
            .where(
                ReportView.report_id == report_id,
                ReportView.viewed_at >= thirty_days_ago
            )
            .group_by(func.date(ReportView.viewed_at))
            .order_by(func.date(ReportView.viewed_at))
        )
        views_by_date_result = await self.db.execute(views_by_date_query)
        views_by_date = {
            str(row.date): row.count 
            for row in views_by_date_result.all()
        }
        
        return ReportViewStats(
            total_views=total_views,
            unique_ips=unique_ips,
            last_viewed_at=last_viewed_at,
            views_by_date=views_by_date
        )
    
    async def get_recent_views(
        self,
        report_id: UUID,
        limit: int = 50
    ) -> List[ReportViewRecord]:
        """
        Получение последних просмотров отчёта.
        
        Args:
            report_id: ID отчёта
            limit: Максимальное количество записей
            
        Returns:
            List[ReportViewRecord]: Список последних просмотров
        """
        query = (
            select(ReportView)
            .where(ReportView.report_id == report_id)
            .order_by(ReportView.viewed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        views = result.scalars().all()
        
        return [
            ReportViewRecord(
                viewed_at=v.viewed_at,
                ip_address=v.ip_address,
                user_agent=v.user_agent
            )
            for v in views
        ]
