"""Сервис для работы с настройками лабораторных работ."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_settings import LabSettings
from app.services.attestation.lab_count_sync import (
    DEFAULT_TOTAL_LABS_COUNT,
    sync_attestation_lab_counts,
)

logger = logging.getLogger(__name__)


class LabSettingsService:
    """Сервис для управления глобальными настройками лаб."""

    async def get_lab_settings(self, db: AsyncSession) -> LabSettings | None:
        """[LabSettingsService:get_lab_settings] Получить глобальные настройки лаб."""
        result = await db.execute(select(LabSettings).limit(1))
        settings = result.scalar_one_or_none()
        logger.info(f"[LabSettingsService:get_lab_settings] Settings found: {settings is not None}")
        return settings

    async def update_lab_settings(self, db: AsyncSession, settings_in) -> LabSettings:
        """[LabSettingsService:update_lab_settings] Обновить или создать настройки лаб."""
        result = await db.execute(select(LabSettings).limit(1))
        settings = result.scalar_one_or_none()

        if not settings:
            settings = LabSettings(
                labs_count=DEFAULT_TOTAL_LABS_COUNT,
                automatic_enabled=True,
                default_max_grade=10,
            )
            db.add(settings)
            await db.flush()
            logger.info("[LabSettingsService:update_lab_settings] Created new settings")

        update_data = settings_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)

        if "labs_count" in update_data:
            await sync_attestation_lab_counts(
                db,
                total_labs=settings.labs_count,
            )

        await db.commit()
        await db.refresh(settings)
        logger.info(f"[LabSettingsService:update_lab_settings] Settings updated: {update_data}")
        return settings


lab_settings_service = LabSettingsService()
