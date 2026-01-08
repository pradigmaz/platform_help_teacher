"""
Модуль управления настройками аттестации.
"""
import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.schemas.attestation import (
    AttestationSettingsUpdate,
    AttestationSettingsResponse,
)

logger = logging.getLogger(__name__)

# Константы кэширования
CACHE_KEY_PREFIX = "attestation:settings"
CACHE_TTL_SECONDS = 300  # 5 минут

# Значения по умолчанию для настроек (Requirements 1.7-1.11)
DEFAULT_SETTINGS = {
    'labs_weight': settings.ATTESTATION_DEFAULT_LABS_WEIGHT,
    'attendance_weight': settings.ATTESTATION_DEFAULT_ATTENDANCE_WEIGHT,
    'activity_weight': settings.ATTESTATION_DEFAULT_ACTIVITY_WEIGHT,
    'required_labs_count': settings.ATTESTATION_DEFAULT_REQUIRED_LABS_COUNT,
    'bonus_per_extra_lab': settings.ATTESTATION_DEFAULT_BONUS_PER_EXTRA_LAB,
    'soft_deadline_penalty': settings.ATTESTATION_DEFAULT_SOFT_DEADLINE_PENALTY,
    'hard_deadline_penalty': settings.ATTESTATION_DEFAULT_HARD_DEADLINE_PENALTY,
    'soft_deadline_days': settings.ATTESTATION_DEFAULT_SOFT_DEADLINE_DAYS,
    'present_points': settings.ATTESTATION_DEFAULT_PRESENT_POINTS,
    'late_points': settings.ATTESTATION_DEFAULT_LATE_POINTS,
    'excused_points': settings.ATTESTATION_DEFAULT_EXCUSED_POINTS,
    'absent_points': settings.ATTESTATION_DEFAULT_ABSENT_POINTS,
    'activity_enabled': settings.ATTESTATION_DEFAULT_ACTIVITY_ENABLED,
    'participation_points': settings.ATTESTATION_DEFAULT_PARTICIPATION_POINTS,
}


def _get_cache_key(attestation_type: AttestationType) -> str:
    """Генерация ключа кэша для типа аттестации."""
    return f"{CACHE_KEY_PREFIX}:{attestation_type.value}"


class AttestationSettingsManager:
    """Менеджер настроек аттестации с кэшированием в Redis."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_from_cache(
        self,
        attestation_type: AttestationType
    ) -> Optional[dict]:
        """Получение настроек из кэша Redis."""
        try:
            redis = await get_redis()
            if redis:
                cached = await redis.get(_get_cache_key(attestation_type))
                if cached:
                    logger.debug(f"Cache hit for attestation settings {attestation_type}")
                    return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")
        return None
    
    async def _set_cache(
        self,
        attestation_type: AttestationType,
        settings_data: dict
    ) -> None:
        """Сохранение настроек в кэш Redis."""
        try:
            redis = await get_redis()
            if redis:
                await redis.setex(
                    _get_cache_key(attestation_type),
                    CACHE_TTL_SECONDS,
                    json.dumps(settings_data, default=str)
                )
                logger.debug(f"Cached attestation settings {attestation_type}")
        except Exception as e:
            logger.warning(f"Redis cache write error: {e}")
    
    async def _invalidate_cache(
        self,
        attestation_type: AttestationType
    ) -> None:
        """Инвалидация кэша при обновлении настроек."""
        try:
            redis = await get_redis()
            if redis:
                await redis.delete(_get_cache_key(attestation_type))
                logger.debug(f"Invalidated cache for attestation settings {attestation_type}")
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    def _settings_to_cache_dict(self, att_settings: AttestationSettings) -> dict:
        """Конвертация модели в словарь для кэша."""
        return {
            'id': str(att_settings.id),
            'attestation_type': att_settings.attestation_type.value,
            'labs_weight': att_settings.labs_weight,
            'attendance_weight': att_settings.attendance_weight,
            'activity_weight': att_settings.activity_weight,
            'required_labs_count': att_settings.required_labs_count,
            'bonus_per_extra_lab': att_settings.bonus_per_extra_lab,
            'soft_deadline_penalty': att_settings.soft_deadline_penalty,
            'hard_deadline_penalty': att_settings.hard_deadline_penalty,
            'soft_deadline_days': att_settings.soft_deadline_days,
            'present_points': att_settings.present_points,
            'late_points': att_settings.late_points,
            'excused_points': att_settings.excused_points,
            'absent_points': att_settings.absent_points,
            'activity_enabled': att_settings.activity_enabled,
            'participation_points': att_settings.participation_points,
            'period_start_date': str(att_settings.period_start_date) if att_settings.period_start_date else None,
            'period_end_date': str(att_settings.period_end_date) if att_settings.period_end_date else None,
        }
    
    async def get_settings(
        self,
        attestation_type: AttestationType
    ) -> Optional[AttestationSettings]:
        """Получение глобальных настроек аттестации."""
        query = select(AttestationSettings).where(
            AttestationSettings.attestation_type == attestation_type
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_settings(
        self,
        attestation_type: AttestationType
    ) -> AttestationSettings:
        """Получение настроек или создание с значениями по умолчанию."""
        att_settings = await self.get_settings(attestation_type)
        
        if att_settings is None:
            att_settings = await self.create_default_settings(attestation_type)
        
        return att_settings
    
    async def create_default_settings(
        self,
        attestation_type: AttestationType
    ) -> AttestationSettings:
        """Создание глобальных настроек по умолчанию для типа аттестации."""
        logger.info(f"Creating default global settings for type {attestation_type}")
        
        att_settings = AttestationSettings(
            attestation_type=attestation_type,
            labs_weight=DEFAULT_SETTINGS['labs_weight'],
            attendance_weight=DEFAULT_SETTINGS['attendance_weight'],
            activity_weight=DEFAULT_SETTINGS['activity_weight'],
            required_labs_count=DEFAULT_SETTINGS['required_labs_count'],
            bonus_per_extra_lab=DEFAULT_SETTINGS['bonus_per_extra_lab'],
            soft_deadline_penalty=DEFAULT_SETTINGS['soft_deadline_penalty'],
            hard_deadline_penalty=DEFAULT_SETTINGS['hard_deadline_penalty'],
            soft_deadline_days=DEFAULT_SETTINGS['soft_deadline_days'],
            present_points=DEFAULT_SETTINGS['present_points'],
            late_points=DEFAULT_SETTINGS['late_points'],
            excused_points=DEFAULT_SETTINGS['excused_points'],
            absent_points=DEFAULT_SETTINGS['absent_points'],
            activity_enabled=DEFAULT_SETTINGS['activity_enabled'],
            participation_points=DEFAULT_SETTINGS['participation_points'],
        )
        
        self.db.add(att_settings)
        await self.db.commit()
        await self.db.refresh(att_settings)
        
        # Кэшируем новые настройки
        await self._set_cache(attestation_type, self._settings_to_cache_dict(att_settings))
        
        return att_settings
    
    async def initialize_settings(
        self
    ) -> tuple[AttestationSettings, AttestationSettings]:
        """Инициализация глобальных настроек аттестации для обоих типов."""
        logger.info("Initializing global attestation settings")
        
        first_settings = await self.get_or_create_settings(AttestationType.FIRST)
        second_settings = await self.get_or_create_settings(AttestationType.SECOND)
        
        return first_settings, second_settings
    
    async def update_settings(
        self,
        settings_update: AttestationSettingsUpdate
    ) -> AttestationSettings:
        """Обновление глобальных настроек аттестации."""
        att_settings = await self.get_or_create_settings(settings_update.attestation_type)
        
        update_data = settings_update.model_dump(exclude={'attestation_type'})
        for field, value in update_data.items():
            setattr(att_settings, field, value)
        
        if not att_settings.validate_weights():
            raise ValueError(
                f"Веса компонентов должны суммироваться в 100%. "
                f"Текущая сумма: {att_settings.labs_weight + att_settings.attendance_weight + att_settings.activity_weight}%"
            )
        
        await self.db.commit()
        await self.db.refresh(att_settings)
        
        # Инвалидируем кэш после обновления
        await self._invalidate_cache(settings_update.attestation_type)
        
        logger.info(f"Updated global attestation settings for type {settings_update.attestation_type}")
        return att_settings
    
    @staticmethod
    def to_response(att_settings: AttestationSettings) -> AttestationSettingsResponse:
        """Преобразование модели в схему ответа с вычисляемыми полями."""
        # Вычисляем периоды на основе semester_start_date
        calculated_period_start = None
        calculated_period_end = None
        if att_settings.semester_start_date:
            period = AttestationSettings.calculate_attestation_period(
                att_settings.semester_start_date,
                att_settings.attestation_type
            )
            calculated_period_start, calculated_period_end = period
        
        return AttestationSettingsResponse(
            id=att_settings.id,
            attestation_type=att_settings.attestation_type,
            labs_weight=att_settings.labs_weight,
            attendance_weight=att_settings.attendance_weight,
            activity_weight=att_settings.activity_weight,
            required_labs_count=att_settings.required_labs_count,
            bonus_per_extra_lab=att_settings.bonus_per_extra_lab,
            soft_deadline_penalty=att_settings.soft_deadline_penalty,
            hard_deadline_penalty=att_settings.hard_deadline_penalty,
            soft_deadline_days=att_settings.soft_deadline_days,
            present_points=att_settings.present_points,
            late_points=att_settings.late_points,
            excused_points=att_settings.excused_points,
            absent_points=att_settings.absent_points,
            activity_enabled=att_settings.activity_enabled,
            participation_points=att_settings.participation_points,
            period_start_date=att_settings.period_start_date,
            period_end_date=att_settings.period_end_date,
            semester_start_date=att_settings.semester_start_date,
            components_config=att_settings.components_config,
            created_at=att_settings.created_at,
            updated_at=att_settings.updated_at,
            max_points=AttestationSettings.get_max_points(att_settings.attestation_type),
            min_passing_points=AttestationSettings.get_min_passing_points(att_settings.attestation_type),
            grade_scale=AttestationSettings.get_grade_scale(att_settings.attestation_type),
            calculated_period_start=calculated_period_start,
            calculated_period_end=calculated_period_end,
        )
