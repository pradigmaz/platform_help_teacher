"""
Модуль управления настройками аттестации (автобалансировка).
"""
import json
import logging
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.schemas.attestation import (
    AttestationSettingsUpdate,
    AttestationSettingsResponse,
    ScorePreview,
)

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "attestation:settings"
CACHE_TTL_SECONDS = 300


def _get_cache_key(attestation_type: AttestationType) -> str:
    return f"{CACHE_KEY_PREFIX}:{attestation_type.value}"


class AttestationSettingsManager:
    """Менеджер настроек аттестации с кэшированием."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _invalidate_cache(self, attestation_type: AttestationType) -> None:
        try:
            redis = await get_redis()
            if redis:
                await redis.delete(_get_cache_key(attestation_type))
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    async def get_settings(self, attestation_type: AttestationType) -> Optional[AttestationSettings]:
        query = select(AttestationSettings).where(
            AttestationSettings.attestation_type == attestation_type
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_settings(self, attestation_type: AttestationType) -> AttestationSettings:
        att_settings = await self.get_settings(attestation_type)
        if att_settings is None:
            att_settings = await self._create_default(attestation_type)
        return att_settings
    
    async def _create_default(self, attestation_type: AttestationType) -> AttestationSettings:
        """Создание настроек по умолчанию."""
        logger.info(f"Creating default settings for {attestation_type}")
        
        att_settings = AttestationSettings(
            attestation_type=attestation_type,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
            grade_4_coef=0.7,
            grade_3_coef=0.4,
            late_coef=0.5,
            late_max_grade=4,
            very_late_max_grade=3,
            late_threshold_days=7,
            self_works_enabled=False,
            self_works_weight=0.0,
            self_works_count=2,
            colloquium_enabled=False,
            colloquium_weight=0.0,
            colloquium_count=1,
            activity_enabled=True,
        )
        
        self.db.add(att_settings)
        await self.db.commit()
        await self.db.refresh(att_settings)
        return att_settings
    
    async def update_settings(self, settings_update: AttestationSettingsUpdate) -> AttestationSettings:
        att_settings = await self.get_or_create_settings(settings_update.attestation_type)
        
        update_data = settings_update.model_dump(exclude={'attestation_type'})
        for field, value in update_data.items():
            setattr(att_settings, field, value)
        
        if not att_settings.validate_weights():
            raise ValueError("Веса должны суммироваться в 100%")
        
        await self.db.commit()
        await self.db.refresh(att_settings)
        await self._invalidate_cache(settings_update.attestation_type)
        
        logger.info(f"Updated settings for {settings_update.attestation_type}")
        return att_settings
    
    @staticmethod
    def build_score_preview(att_settings: AttestationSettings) -> List[ScorePreview]:
        """Построение превью расчёта баллов для UI."""
        previews = []
        labs_count = att_settings.get_labs_count()
        
        # Лабораторные
        labs_max = att_settings.get_max_component_points(att_settings.labs_weight)
        labs_per_work = att_settings.get_points_per_work(att_settings.labs_weight, labs_count)
        previews.append(ScorePreview(
            component=f"Лабораторные ({labs_count})",
            weight=att_settings.labs_weight,
            max_points=round(labs_max, 2),
            points_per_unit=round(labs_per_work, 2),
            unit_label="за 5"
        ))
        
        # Посещаемость
        att_max = att_settings.get_max_component_points(att_settings.attendance_weight)
        previews.append(ScorePreview(
            component="Посещаемость",
            weight=att_settings.attendance_weight,
            max_points=round(att_max, 2),
            points_per_unit=100.0,
            unit_label="% от посещённых"
        ))
        
        # Резерв активности
        reserve_max = att_settings.get_max_component_points(att_settings.activity_reserve)
        previews.append(ScorePreview(
            component="Резерв (активность)",
            weight=att_settings.activity_reserve,
            max_points=round(reserve_max, 2),
            points_per_unit=0.0,
            unit_label="бонусы/штрафы"
        ))
        
        # Опциональные компоненты
        if att_settings.self_works_enabled:
            sw_max = att_settings.get_max_component_points(att_settings.self_works_weight)
            sw_per = att_settings.get_points_per_work(att_settings.self_works_weight, att_settings.self_works_count)
            previews.append(ScorePreview(
                component=f"СР ({att_settings.self_works_count})",
                weight=att_settings.self_works_weight,
                max_points=round(sw_max, 2),
                points_per_unit=round(sw_per, 2),
                unit_label="за 5"
            ))
        
        if att_settings.colloquium_enabled:
            coll_max = att_settings.get_max_component_points(att_settings.colloquium_weight)
            coll_per = att_settings.get_points_per_work(att_settings.colloquium_weight, att_settings.colloquium_count)
            previews.append(ScorePreview(
                component=f"Коллоквиум ({att_settings.colloquium_count})",
                weight=att_settings.colloquium_weight,
                max_points=round(coll_max, 2),
                points_per_unit=round(coll_per, 2),
                unit_label="за 5"
            ))
        
        return previews
    
    @staticmethod
    def to_response(att_settings: AttestationSettings) -> AttestationSettingsResponse:
        """Преобразование модели в схему ответа."""
        calculated_start, calculated_end = None, None
        if att_settings.semester_start_date:
            calculated_start, calculated_end = AttestationSettings.calculate_attestation_period(
                att_settings.semester_start_date,
                att_settings.attestation_type
            )
        
        return AttestationSettingsResponse(
            id=att_settings.id,
            attestation_type=att_settings.attestation_type,
            labs_weight=att_settings.labs_weight,
            attendance_weight=att_settings.attendance_weight,
            activity_reserve=att_settings.activity_reserve,
            labs_count_first=att_settings.labs_count_first,
            labs_count_second=att_settings.labs_count_second,
            grade_4_coef=att_settings.grade_4_coef,
            grade_3_coef=att_settings.grade_3_coef,
            late_coef=att_settings.late_coef,
            late_max_grade=att_settings.late_max_grade,
            very_late_max_grade=att_settings.very_late_max_grade,
            late_threshold_days=att_settings.late_threshold_days,
            self_works_enabled=att_settings.self_works_enabled,
            self_works_weight=att_settings.self_works_weight,
            self_works_count=att_settings.self_works_count,
            colloquium_enabled=att_settings.colloquium_enabled,
            colloquium_weight=att_settings.colloquium_weight,
            colloquium_count=att_settings.colloquium_count,
            activity_enabled=att_settings.activity_enabled,
            period_start_date=att_settings.period_start_date,
            period_end_date=att_settings.period_end_date,
            semester_start_date=att_settings.semester_start_date,
            created_at=att_settings.created_at,
            updated_at=att_settings.updated_at,
            max_points=att_settings.attestation_type.max_points,
            min_passing_points=AttestationSettings.get_min_passing_points(att_settings.attestation_type),
            grade_scale=AttestationSettings.get_grade_scale(att_settings.attestation_type),
            score_preview=AttestationSettingsManager.build_score_preview(att_settings),
            calculated_period_start=calculated_start,
            calculated_period_end=calculated_end,
        )
