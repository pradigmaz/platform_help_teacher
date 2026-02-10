"""
User Service - бизнес-логика для работы с пользователями.

Паттерн: Endpoint → Service → CRUD → Model
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.crud import crud_user

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для работы с пользователями."""

    async def create_user(
        self,
        db: AsyncSession,
        user_in: schemas.UserCreate,
    ) -> models.User:
        """
        Создание нового пользователя.

        Args:
            db: Сессия БД
            user_in: Данные для создания пользователя

        Returns:
            Созданный пользователь

        Raises:
            HTTPException: Если пользователь с таким social_id уже существует
            HTTPException: При ошибке БД
        """
        logger.info(f"[UserService:create_user] Creating user with social_id={user_in.social_id}")

        # 1. Проверка существования пользователя
        existing_user = await crud_user.get_by_social_id(db, user_in.social_id)
        if existing_user:
            logger.warning(f"[UserService:create_user] User with social_id={user_in.social_id} already exists")
            raise HTTPException(status_code=400, detail="User with this social ID already exists")

        # 2. Поиск группы по коду (если указан)
        group_id = None
        if user_in.group_code:
            logger.info(f"[UserService:create_user] Looking for group with code={user_in.group_code}")
            group_result = await db.execute(select(models.Group).where(models.Group.code == user_in.group_code))
            group = group_result.scalar_one_or_none()
            if group:
                group_id = group.id
                logger.info(f"[UserService:create_user] Found group_id={group_id}")
            else:
                logger.warning(f"[UserService:create_user] Group with code={user_in.group_code} not found")

        try:
            # 3. Создание пользователя
            user = models.User(
                social_id=user_in.social_id,
                full_name=user_in.full_name,
                username=user_in.username,
                role=user_in.role,
                group_id=group_id,
                is_active=True,
            )
            db.add(user)

            # 4. Фиксация транзакции
            await db.commit()
            await db.refresh(user)

            logger.info(f"[UserService:create_user] User created successfully: id={user.id}")
            return user

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"[UserService:create_user] Database error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during user creation"
            )

    async def update_user(
        self,
        db: AsyncSession,
        user: models.User,
        user_in: schemas.UserUpdate,
    ) -> models.User:
        """
        Обновление данных пользователя.

        Args:
            db: Сессия БД
            user: Текущий пользователь
            user_in: Данные для обновления

        Returns:
            Обновленный пользователь

        Raises:
            HTTPException: При ошибке БД
        """
        logger.info(f"[UserService:update_user] Updating user id={user.id}")

        try:
            # Обновляем только переданные поля
            if user_in.full_name is not None:
                logger.info(f"[UserService:update_user] Updating full_name for user id={user.id}")
                user.full_name = user_in.full_name

            if user_in.onboarding_completed is not None:
                logger.info(
                    f"[UserService:update_user] Updating onboarding_completed={user_in.onboarding_completed} for user id={user.id}"
                )
                user.onboarding_completed = user_in.onboarding_completed

            await db.commit()
            await db.refresh(user)

            logger.info(f"[UserService:update_user] User updated successfully: id={user.id}")
            return user

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"[UserService:update_user] Database error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during user update"
            )

    async def update_contacts(
        self,
        db: AsyncSession,
        user: models.User,
        contacts_data: schemas.TeacherContactsUpdate,
    ) -> models.User:
        """
        Обновление контактов преподавателя.

        Args:
            db: Сессия БД
            user: Текущий пользователь (преподаватель)
            contacts_data: Новые контакты и настройки видимости

        Returns:
            Обновленный пользователь

        Raises:
            HTTPException: При ошибке БД
        """
        logger.info(f"[UserService:update_contacts] Updating contacts for user id={user.id}")

        try:
            user.contacts = contacts_data.contacts.model_dump(exclude_none=True)
            user.contact_visibility = contacts_data.visibility.model_dump()

            await db.commit()
            await db.refresh(user)

            logger.info(f"[UserService:update_contacts] Contacts updated successfully for user id={user.id}")
            return user

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"[UserService:update_contacts] Database error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during contacts update"
            )

    async def update_settings(
        self,
        db: AsyncSession,
        user: models.User,
        hide_previous_semester: bool | None = None,
    ) -> models.User:
        """
        Обновление настроек преподавателя.

        Args:
            db: Сессия БД
            user: Текущий пользователь (преподаватель)
            hide_previous_semester: Скрывать ли прошлый семестр

        Returns:
            Обновленный пользователь

        Raises:
            HTTPException: При ошибке БД
        """
        logger.info(f"[UserService:update_settings] Updating settings for user id={user.id}")

        try:
            settings = user.teacher_settings or {}

            if hide_previous_semester is not None:
                logger.info(
                    f"[UserService:update_settings] Setting hide_previous_semester={hide_previous_semester} for user id={user.id}"
                )
                settings["hide_previous_semester"] = hide_previous_semester

            user.teacher_settings = settings

            await db.commit()
            await db.refresh(user)

            logger.info(f"[UserService:update_settings] Settings updated successfully for user id={user.id}")
            return user

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"[UserService:update_settings] Database error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during settings update"
            )


# Singleton instance
user_service = UserService()
