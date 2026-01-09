"""
Аудит изменений настроек аттестации.
"""
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings_audit import SettingsAuditLog
from app.models.attestation_settings import AttestationSettings, AttestationType

logger = logging.getLogger(__name__)


class AttestationAuditService:
    """Сервис аудита настроек аттестации."""
    
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
        """Логирование изменения настроек."""
        old_values = self._settings_to_dict(old_settings) if old_settings else None
        new_values = self._settings_to_dict(new_settings)
        
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
        
        logger.info(f"Audit: {action} attestation '{attestation_type.value}' by {changed_by_id}")
        return audit_log
    
    def _settings_to_dict(self, settings: AttestationSettings) -> Dict[str, Any]:
        """Конвертация настроек в словарь."""
        return {
            'labs_weight': settings.labs_weight,
            'attendance_weight': settings.attendance_weight,
            'activity_reserve': settings.activity_reserve,
            'labs_count_first': settings.labs_count_first,
            'labs_count_second': settings.labs_count_second,
            'grade_4_coef': settings.grade_4_coef,
            'grade_3_coef': settings.grade_3_coef,
            'late_coef': settings.late_coef,
            'late_max_grade': settings.late_max_grade,
            'very_late_max_grade': settings.very_late_max_grade,
            'late_threshold_days': settings.late_threshold_days,
            'self_works_enabled': settings.self_works_enabled,
            'self_works_weight': settings.self_works_weight,
            'self_works_count': settings.self_works_count,
            'colloquium_enabled': settings.colloquium_enabled,
            'colloquium_weight': settings.colloquium_weight,
            'colloquium_count': settings.colloquium_count,
            'activity_enabled': settings.activity_enabled,
            'period_start_date': str(settings.period_start_date) if settings.period_start_date else None,
            'period_end_date': str(settings.period_end_date) if settings.period_end_date else None,
            'semester_start_date': str(settings.semester_start_date) if settings.semester_start_date else None,
        }
    
    async def get_audit_history(
        self,
        attestation_type: Optional[AttestationType] = None,
        limit: int = 50
    ) -> List[SettingsAuditLog]:
        """Получение истории изменений."""
        query = (
            select(SettingsAuditLog)
            .where(SettingsAuditLog.settings_type == self.SETTINGS_TYPE)
            .order_by(SettingsAuditLog.created_at.desc())
            .limit(limit)
        )
        
        if attestation_type:
            query = query.where(SettingsAuditLog.settings_key == attestation_type.value)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
