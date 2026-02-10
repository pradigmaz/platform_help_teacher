"""
Примеры использования error_messages.py

Этот файл показывает, как правильно использовать централизованные сообщения об ошибках.
"""

from fastapi import HTTPException, status
from app.core import error_messages as em


# ============================================================================
# Пример 1: Простое использование
# ============================================================================

def get_user(user_id: int):
    """Пример использования простого сообщения."""
    user = None  # Имитация поиска в БД
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=em.USER_NOT_FOUND
        )


# ============================================================================
# Пример 2: Сообщение с параметрами
# ============================================================================

def validate_file_type(file_type: str, allowed_types: list[str]):
    """Пример использования сообщения с форматированием."""
    if file_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=em.format_error(em.FILE_TYPE_NOT_ALLOWED, type=file_type)
        )


# ============================================================================
# Пример 3: Использование в логировании
# ============================================================================

import logging

logger = logging.getLogger(__name__)


def process_file(file_size: int, max_size: int):
    """Пример использования в логах."""
    if file_size > max_size:
        error_msg = em.format_error(em.FILE_TOO_LARGE, max=f"{max_size} bytes")
        logger.error(f"[Files:validate] {error_msg}", extra={
            "file_size": file_size,
            "max_size": max_size
        })
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg
        )


# ============================================================================
# Пример 4: Использование в сервисах
# ============================================================================

class GroupService:
    """Пример использования в сервисном слое."""
    
    async def get_group(self, group_id: int):
        """Получить группу по ID."""
        group = None  # Имитация поиска
        
        if not group:
            logger.warning(f"[GroupService:get_group] {em.GROUP_NOT_FOUND}", extra={
                "group_id": group_id
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=em.GROUP_NOT_FOUND
            )
        
        return group


# ============================================================================
# Пример 5: Множественные проверки
# ============================================================================

def validate_permissions(user_role: str, required_role: str):
    """Пример цепочки проверок."""
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=em.USER_NOT_FOUND
        )
    
    if user_role != required_role:
        logger.warning(f"[Auth:validate] {em.NOT_ENOUGH_PERMISSIONS}", extra={
            "user_role": user_role,
            "required_role": required_role
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=em.NOT_ENOUGH_PERMISSIONS
        )


# ============================================================================
# Пример 6: Использование в CRUD
# ============================================================================

class LabCRUD:
    """Пример использования в CRUD слое."""
    
    async def get_lab(self, lab_id: int):
        """Получить лабораторную работу."""
        lab = None  # Имитация запроса к БД
        
        if not lab:
            raise ValueError(em.LAB_NOT_FOUND)  # В CRUD используем ValueError
        
        return lab


# ============================================================================
# Пример 7: Кастомные ошибки с контекстом
# ============================================================================

def check_lab_availability(lab, current_date):
    """Проверка доступности лабораторной работы."""
    if lab.available_from and current_date < lab.available_from:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=em.LAB_NOT_AVAILABLE_YET
        )
    
    if not lab.is_available_by_schedule:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=em.LAB_NOT_AVAILABLE_BY_SCHEDULE
        )
