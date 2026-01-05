"""
Основной сервис для управления публичными отчётами.

Фасад для работы с отчётами, объединяющий все модули.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    PublicReportData,
    StudentDetailData,
    ReportViewStats,
    ReportViewRecord,
)

from .security import generate_code, hash_pin, verify_pin
from .audit import ReportAuditService
from .data_collector import ReportDataCollector

logger = logging.getLogger(__name__)


class ReportService:
    """
    Сервис для работы с публичными отчётами.
    
    Объединяет функциональность:
    - security: генерация кодов, работа с PIN
    - audit: логирование просмотров
    - data_collector: сбор данных для отчётов
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = ReportAuditService(db)
        self._collector = ReportDataCollector(db)
    
    # ==================== Static Methods ====================
    
    @staticmethod
    def generate_code() -> str:
        """Генерация криптографически безопасного 8-символьного кода."""
        return generate_code()
    
    @staticmethod
    def hash_pin(pin: str) -> str:
        """Хеширование PIN-кода."""
        return hash_pin(pin)
    
    @staticmethod
    def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
        """Проверка PIN-кода."""
        return verify_pin(plain_pin, hashed_pin)
    
    # ==================== Report CRUD ====================
    
    async def generate_unique_code(self) -> str:
        """Генерация уникального кода с проверкой в БД."""
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_code()
            existing = await self.db.execute(
                select(GroupReport.id).where(GroupReport.code == code)
            )
            if existing.scalar_one_or_none() is None:
                return code
        
        raise RuntimeError("Failed to generate unique code after max attempts")
    
    async def create_report(
        self,
        group_id: UUID,
        teacher_id: UUID,
        settings: ReportCreate
    ) -> GroupReport:
        """Создание нового публичного отчёта."""
        code = await self.generate_unique_code()
        
        expires_at = None
        if settings.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.expires_in_days)
        
        pin_hash = None
        if settings.pin_code:
            pin_hash = hash_pin(settings.pin_code)
        
        report = GroupReport(
            group_id=group_id,
            created_by=teacher_id,
            code=code,
            report_type=settings.report_type.value,
            expires_at=expires_at,
            pin_hash=pin_hash,
            show_names=settings.show_names,
            show_grades=settings.show_grades,
            show_attendance=settings.show_attendance,
            show_notes=settings.show_notes,
            show_rating=settings.show_rating,
        )
        
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        
        logger.info(f"Created report {code} for group {group_id} by teacher {teacher_id}")
        return report
    
    async def get_report_by_code(
        self,
        code: str,
        check_active: bool = True,
        check_expiry: bool = True
    ) -> Optional[GroupReport]:
        """Получение отчёта по коду с проверками."""
        query = select(GroupReport).where(GroupReport.code == code)
        
        if check_active:
            query = query.where(GroupReport.is_active == True)
        
        result = await self.db.execute(query)
        report = result.scalar_one_or_none()
        
        if report is None:
            return None
        
        if check_expiry and report.expires_at:
            if datetime.now(timezone.utc) > report.expires_at:
                logger.info(f"Report {code} has expired")
                return None
        
        return report
    
    async def get_report_by_id(self, report_id: UUID) -> Optional[GroupReport]:
        """Получение отчёта по ID."""
        query = select(GroupReport).where(GroupReport.id == report_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_reports_by_teacher(self, teacher_id: UUID) -> List[GroupReport]:
        """Получение всех отчётов преподавателя."""
        query = (
            select(GroupReport)
            .where(GroupReport.created_by == teacher_id)
            .order_by(GroupReport.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_report(
        self,
        report: GroupReport,
        update_data: ReportUpdate
    ) -> GroupReport:
        """Обновление настроек отчёта."""
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if update_data.remove_pin:
            report.pin_hash = None
        elif update_data.pin_code:
            report.pin_hash = hash_pin(update_data.pin_code)
        
        if 'expires_in_days' in update_dict and update_dict['expires_in_days']:
            report.expires_at = datetime.now(timezone.utc) + timedelta(
                days=update_dict['expires_in_days']
            )
        
        for field in ['show_names', 'show_grades', 'show_attendance', 
                      'show_notes', 'show_rating', 'is_active']:
            if field in update_dict and update_dict[field] is not None:
                setattr(report, field, update_dict[field])
        
        await self.db.commit()
        await self.db.refresh(report)
        
        logger.info(f"Updated report {report.code}")
        return report
    
    async def deactivate_report(self, report: GroupReport) -> GroupReport:
        """Деактивация отчёта."""
        report.is_active = False
        await self.db.commit()
        await self.db.refresh(report)
        logger.info(f"Deactivated report {report.code}")
        return report
    
    async def regenerate_code(self, report: GroupReport) -> GroupReport:
        """Генерация нового кода для отчёта."""
        old_code = report.code
        report.code = await self.generate_unique_code()
        await self.db.commit()
        await self.db.refresh(report)
        logger.info(f"Regenerated code for report: {old_code} -> {report.code}")
        return report
    
    # ==================== Data Collection (delegated) ====================
    
    async def get_group_report_data(self, report: GroupReport) -> PublicReportData:
        """Сбор данных для публичного отчёта группы."""
        return await self._collector.get_group_report_data(report)
    
    async def get_student_report_data(
        self,
        report: GroupReport,
        student_id: UUID
    ) -> Optional[StudentDetailData]:
        """Сбор детальных данных для отчёта по студенту."""
        return await self._collector.get_student_report_data(report, student_id)
    
    def apply_visibility_filter(self, data: dict, report: GroupReport) -> dict:
        """Применение фильтра видимости к данным."""
        return self._collector.apply_visibility_filter(data, report)
    
    # ==================== Audit (delegated) ====================
    
    async def log_view(
        self,
        report_id: UUID,
        ip_address: str,
        user_agent: Optional[str] = None
    ):
        """Логирование просмотра отчёта."""
        return await self._audit.log_view(report_id, ip_address, user_agent)
    
    async def get_view_stats(self, report_id: UUID) -> ReportViewStats:
        """Получение статистики просмотров отчёта."""
        return await self._audit.get_view_stats(report_id)
    
    async def get_recent_views(
        self,
        report_id: UUID,
        limit: int = 50
    ) -> List[ReportViewRecord]:
        """Получение последних просмотров отчёта."""
        return await self._audit.get_recent_views(report_id, limit)
