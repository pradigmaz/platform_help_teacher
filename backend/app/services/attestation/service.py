"""
Сервис для управления настройками аттестации и расчёта баллов.
Фасад для модулей settings, student_score, batch.

Реализует Requirements 5.1, 5.2 - API для получения и обновления настроек.
Реализует Requirements 6.1-6.3 - расчёт баллов для студентов и групп.
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

from .settings import AttestationSettingsManager, DEFAULT_SETTINGS
from .student_score import StudentScoreCalculator
from .batch import BatchScoreCalculator
from .calculator import AttestationCalculator


class AttestationService:
    """
    Сервис для работы с настройками аттестации и расчётом баллов.
    
    Методы:
    - get_settings: получение настроек для типа аттестации
    - update_settings: обновление настроек аттестации
    - get_or_create_settings: получение или создание настроек по умолчанию
    - calculate_student_score: расчёт баллов для студента
    - calculate_group_scores_batch: пакетный расчёт баллов для группы
    - calculate_all_students_scores: расчёт баллов для всех студентов
    """
    
    DEFAULT_SETTINGS = DEFAULT_SETTINGS
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = AttestationCalculator()
        self._settings_manager = AttestationSettingsManager(db)
        self._student_calculator = StudentScoreCalculator(db)
        self._batch_calculator = BatchScoreCalculator(db)
    
    # ==================== Settings Methods ====================
    
    async def get_settings(
        self,
        attestation_type: AttestationType
    ) -> Optional[AttestationSettings]:
        """Получение глобальных настроек аттестации."""
        return await self._settings_manager.get_settings(attestation_type)
    
    async def get_or_create_settings(
        self,
        attestation_type: AttestationType
    ) -> AttestationSettings:
        """Получение настроек или создание с значениями по умолчанию."""
        return await self._settings_manager.get_or_create_settings(attestation_type)
    
    async def create_default_settings(
        self,
        attestation_type: AttestationType
    ) -> AttestationSettings:
        """Создание глобальных настроек по умолчанию для типа аттестации."""
        return await self._settings_manager.create_default_settings(attestation_type)
    
    async def initialize_settings(
        self
    ) -> tuple[AttestationSettings, AttestationSettings]:
        """Инициализация глобальных настроек аттестации для обоих типов."""
        return await self._settings_manager.initialize_settings()
    
    async def update_settings(
        self,
        settings_update: AttestationSettingsUpdate
    ) -> AttestationSettings:
        """Обновление глобальных настроек аттестации."""
        return await self._settings_manager.update_settings(settings_update)
    
    def to_response(self, att_settings: AttestationSettings) -> AttestationSettingsResponse:
        """Преобразование модели в схему ответа с вычисляемыми полями."""
        return AttestationSettingsManager.to_response(att_settings)

    # ==================== Calculation Methods ====================

    async def calculate_student_score(
        self,
        student_id: UUID,
        group_id: UUID,
        attestation_type: AttestationType,
        activity_points: float = 0.0
    ) -> AttestationResult:
        """Расчёт баллов аттестации для студента."""
        return await self._student_calculator.calculate(
            student_id, group_id, attestation_type, activity_points
        )

    async def calculate_all_students_scores(
        self,
        attestation_type: AttestationType
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Расчёт баллов для ВСЕХ студентов (все группы).
        Сортировка по ФИО (А-Я).
        """
        return await self._batch_calculator.calculate_all_students(attestation_type)

    async def calculate_group_scores_batch(
        self,
        group_id: UUID,
        attestation_type: AttestationType,
        students: Optional[List[User]] = None
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Пакетный расчёт баллов для группы.
        Optimized to avoid N+1 queries.
        """
        return await self._batch_calculator.calculate_group_batch(
            group_id, attestation_type, students
        )
