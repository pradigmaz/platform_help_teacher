"""
Модуль аудита изменений настроек аттестации.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings_audit import SettingsAuditLog
from app.models.attestation_settings import AttestationSettings, AttestationType

logger = logging.getLogger(__name__)


class AttestationAuditService:
    """Сервис аудита изменений настроек аттестации."""
    
    SETTINGS_TYPE = "attestation"
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_settings_change(
        self,
        attestation_type: AttestationType,
        action: str,
        old_settings: Optional[AttestationSettings],
        new_settings: AttestationSettings,
        changed_by_id: UUID,
        ip_address: Optional[str] = None
    ) -> SettingsAuditLog:
        """
        Логирование изменения настроек аттестации.
        
        Args:
            attestation_type: Тип аттестации
            action: Действие (create, update)
            old_settings: Старые настройки (None для create)
            new_settings: Новые настройки
            changed_by_id: ID пользователя
            ip_address: IP адрес
            
        Returns:
            SettingsAuditLog: Созданная запись
        """
        old_values = self._settings_to_dict(old_settings) if old_settings else None
        new_values = self._settings_to_dict(new_settings)
        
        # Определяем изменённые поля
        changed_fields = None
        if old_values and new_values:
            changed_fields = [
                key for key in new_values
                if key in old_values and old_values[key] != new_values[key]
            ]
        
        audit_log = SettingsAuditLog(
            settings_type=self.SETTINGS_TYPE,
            settings_key=attestation_type.value,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            changed_by_id=changed_by_id,
            ip_address=ip_address
        )
        
        self.db.add(audit_log)
        await self.db.flush()
        
        logger.info(
            f"Audit log: {action} attestation settings '{attestation_type.value}' "
            f"by user {changed_by_id}, changed fields: {changed_fields}"
        )
        
        return audit_log
    
    def _settings_to_dict(self, settings: AttestationSettings) -> Dict[str, Any]:
        """Конвертация настроек в словарь для логирования."""
        return {
            'labs_weight': settings.labs_weight,
            'attendance_weight': settings.attendance_weight,
            'activity_weight': settings.activity_weight,
            'required_labs_count': settings.required_labs_count,
            'bonus_per_extra_lab': settings.bonus_per_extra_lab,
            'soft_deadline_penalty': settings.soft_deadline_penalty,
            'hard_deadline_penalty': settings.hard_deadline_penalty,
            'soft_deadline_days': settings.soft_deadline_days,
            'present_points': settings.present_points,
            'late_points': settings.late_points,
            'excused_points': settings.excused_points,
            'absent_points': settings.absent_points,
            'activity_enabled': settings.activity_enabled,
            'participation_points': settings.participation_points,
            'period_start_date': str(settings.period_start_date) if settings.period_start_date else None,
            'period_end_date': str(settings.period_end_date) if settings.period_end_date else None,
        }
    
    async def get_audit_history(
        self,
        attestation_type: Optional[AttestationType] = None,
        limit: int = 50
    ) -> List[SettingsAuditLog]:
        """
        Получение истории изменений настроек.
        
        Args:
            attestation_type: Фильтр по типу аттестации (опционально)
            limit: Максимальное количество записей
            
        Returns:
            List[SettingsAuditLog]: Список записей аудита
        """
        query = (
            select(SettingsAuditLog)
            .where(SettingsAuditLog.settings_type == self.SETTINGS_TYPE)
            .order_by(SettingsAuditLog.created_at.desc())
            .limit(limit)
        )
        
        if attestation_type:
            query = query.where(
                SettingsAuditLog.settings_key == attestation_type.value
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
