"""
Сервис аттестации (фасад).
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.user import User
from app.schemas.attestation import (
    AttestationSettingsUpdate,
    AttestationSettingsResponse,
    AttestationResult,
    CalculationErrorInfo,
)

from .settings import AttestationSettingsManager
from .student_score import StudentScoreCalculator
from .batch import BatchScoreCalculator
from .calculator import AttestationCalculator


class AttestationService:
    """Сервис для настроек и расчёта баллов аттестации."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = AttestationCalculator()
        self._settings_manager = AttestationSettingsManager(db)
        self._student_calculator = StudentScoreCalculator(db)
        self._batch_calculator = BatchScoreCalculator(db)
    
    # === Settings ===
    
    async def get_settings(self, attestation_type: AttestationType) -> Optional[AttestationSettings]:
        return await self._settings_manager.get_settings(attestation_type)
    
    async def get_or_create_settings(self, attestation_type: AttestationType) -> AttestationSettings:
        return await self._settings_manager.get_or_create_settings(attestation_type)
    
    async def update_settings(self, settings_update: AttestationSettingsUpdate) -> AttestationSettings:
        return await self._settings_manager.update_settings(settings_update)
    
    def to_response(self, att_settings: AttestationSettings) -> AttestationSettingsResponse:
        return AttestationSettingsManager.to_response(att_settings)

    # === Calculation ===

    async def calculate_student_score(
        self,
        student_id: UUID,
        group_id: UUID,
        attestation_type: AttestationType,
        activity_points: float = 0.0
    ) -> AttestationResult:
        return await self._student_calculator.calculate(
            student_id, group_id, attestation_type, activity_points
        )

    async def calculate_group_scores_batch(
        self,
        group_id: UUID,
        attestation_type: AttestationType,
        students: Optional[List[User]] = None
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        return await self._batch_calculator.calculate_group_batch(
            group_id, attestation_type, students
        )
