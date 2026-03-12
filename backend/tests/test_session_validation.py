"""
Тесты для валидации сессий в get_current_user.

Проверяет:
1. Валидный session → 200 OK, user возвращается
2. Отозванный session (revoked) → 401 "Session revoked"
3. Без session cookie → 401 "Session revoked"
4. Expired session в Redis → 401 "Session revoked"
5. JWT валиден, но session_id не существует в Redis → 401
6. JWT subject должен совпадать с владельцем session
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core.config import settings
from app.models import User, UserRole
from app.services import session_service

# ============================================================================
# Helpers
# ============================================================================


def create_jwt_token(user_id: UUID, expires_delta: timedelta = None) -> str:
    """
    Создать JWT токен для тестирования.

    Args:
        user_id: ID пользователя
        expires_delta: Время жизни токена (по умолчанию 15 минут)

    Returns:
        JWT токен строкой
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=15)

    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_mock_request(
    token: str = None, session_id: str = None, client_ip: str = "127.0.0.1", path: str = "/api/test"
) -> Mock:
    """
    Создать мок Request объект.

    Args:
        token: JWT токен (в cookie access_token)
        session_id: Session ID (в cookie audit_session_id)
        client_ip: IP адрес клиента
        path: Путь запроса

    Returns:
        Mock объект Request
    """
    request = Mock(spec=Request)
    request.cookies = {}

    if token:
        request.cookies["access_token"] = token
    if session_id:
        request.cookies[SESSION_COOKIE_NAME] = session_id

    request.client = Mock(host=client_ip)
    request.url = Mock(path=path)
    request.state = Mock()

    return request


def create_mock_user(user_id: UUID = None, role: UserRole = UserRole.STUDENT, is_active: bool = True) -> User:
    """
    Создать мок User объект.

    Args:
        user_id: ID пользователя (генерируется если не указан)
        role: Роль пользователя
        is_active: Активен ли пользователь

    Returns:
        User объект
    """
    if user_id is None:
        user_id = uuid4()

    user = User(
        id=user_id,
        full_name="Test User",
        username="testuser",
        role=role,
        is_active=is_active,
    )
    return user


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_user():
    """Тестовый пользователь."""
    return create_mock_user()


@pytest.fixture
def mock_db_session():
    """Мок database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def valid_session_data(test_user):
    """Валидные данные сессии."""
    return {
        "user_id": str(test_user.id),
        "created_at": datetime.now(UTC).isoformat(),
        "device_fingerprint": "test_fingerprint",
        "ip_address": "127.0.0.1",
        "is_impersonation": False,
    }


# ============================================================================
# Tests: Валидная сессия
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_with_valid_session(test_user, mock_db_session, valid_session_data):
    """
    Тест: Валидный JWT + валидная сессия → пользователь возвращается.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "valid_session_123"
    request = create_mock_request(token=token, session_id=session_id)

    # Mock DB query
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=test_user)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Mock session validation
    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = valid_session_data

        # Act
        user = await get_current_user(request, mock_db_session)

        # Assert
        assert user.id == test_user.id
        assert user.username == test_user.username
        mock_validate.assert_called_once_with(session_id, expected_user_id=str(test_user.id))


@pytest.mark.asyncio
async def test_get_current_user_with_valid_session_logs_debug(test_user, mock_db_session, valid_session_data, caplog):
    """
    Тест: Валидная сессия логирует debug сообщение.
    """
    # Arrange
    import logging

    caplog.set_level(logging.DEBUG)

    token = create_jwt_token(test_user.id)
    session_id = "valid_session_456"
    request = create_mock_request(token=token, session_id=session_id)

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=test_user)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = valid_session_data

        # Act
        await get_current_user(request, mock_db_session)

        # Assert
        assert "Session validated" in caplog.text
        assert session_id[:8] in caplog.text


# ============================================================================
# Tests: Отозванная сессия
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_with_revoked_session(test_user, mock_db_session):
    """
    Тест: JWT валиден, но сессия отозвана → 401 "Session revoked".
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "revoked_session_123"
    request = create_mock_request(token=token, session_id=session_id)

    # Mock session validation returns None (revoked)
    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, mock_db_session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Session revoked"
        assert request.state.auth_error_reason == "session_revoked"


@pytest.mark.asyncio
async def test_get_current_user_with_revoked_session_logs_warning(test_user, mock_db_session, caplog):
    """
    Тест: Отозванная сессия логирует warning с деталями.
    """
    # Arrange
    import logging

    caplog.set_level(logging.WARNING)

    token = create_jwt_token(test_user.id)
    session_id = "revoked_session_456"
    request = create_mock_request(token=token, session_id=session_id)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None

        # Act
        with pytest.raises(HTTPException):
            await get_current_user(request, mock_db_session)

        # Assert
        assert "Auth failed: session revoked" in caplog.text
        assert str(test_user.id) in caplog.text
        assert session_id[:8] in caplog.text


# ============================================================================
# Tests: Без session cookie
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_without_session_cookie(test_user, mock_db_session):
    """
    Тест: JWT валиден, но нет session cookie → 401.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    request = create_mock_request(token=token, session_id=None)

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, mock_db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session revoked"
    assert request.state.auth_error_reason == "session_missing"
    mock_db_session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_without_session_cookie_logs_warning(test_user, mock_db_session, caplog):
    """
    Тест: Отсутствие session cookie логирует warning и отклоняет запрос.
    """
    # Arrange
    import logging

    caplog.set_level(logging.WARNING)

    token = create_jwt_token(test_user.id)
    request = create_mock_request(token=token, session_id=None)

    with pytest.raises(HTTPException):
        await get_current_user(request, mock_db_session)

    assert "No session cookie found" in caplog.text
    assert str(test_user.id) in caplog.text
    mock_db_session.execute.assert_not_awaited()


# ============================================================================
# Tests: Expired session в Redis
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_with_expired_session_in_redis(test_user, mock_db_session):
    """
    Тест: JWT валиден, но session истекла в Redis → 401 "Session revoked".

    Когда сессия истекает в Redis, validate_session возвращает None.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "expired_session_123"
    request = create_mock_request(token=token, session_id=session_id)

    # Mock session validation returns None (expired in Redis)
    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, mock_db_session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Session revoked"
        assert request.state.auth_error_reason == "session_revoked"


# ============================================================================
# Tests: JWT валиден, но session_id не существует
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_with_nonexistent_session_id(test_user, mock_db_session):
    """
    Тест: JWT валиден, но session_id не существует в Redis → 401.

    Это может произойти если:
    - Redis был очищен
    - Session ID подделан
    - Session была удалена вручную
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "nonexistent_session_999"
    request = create_mock_request(token=token, session_id=session_id)

    # Mock session validation returns None (doesn't exist)
    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, mock_db_session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Session revoked"


@pytest.mark.asyncio
async def test_get_current_user_with_session_owner_mismatch(
    test_user,
    mock_db_session,
):
    """
    Тест: JWT валиден, но session принадлежит другому пользователю → 401.
    """
    token = create_jwt_token(test_user.id)
    session_id = "wrong_owner_session"
    request = create_mock_request(token=token, session_id=session_id)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {
            "user_id": str(uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "is_impersonation": False,
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, mock_db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session revoked"
    assert request.state.auth_error_reason == "session_owner_mismatch"
    mock_db_session.execute.assert_not_awaited()


# ============================================================================
# Tests: Комбинированные сценарии
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_session_validation_called_before_db_query(
    test_user, mock_db_session, valid_session_data
):
    """
    Тест: Валидация сессии происходит ДО запроса к БД.

    Это важно для производительности - не нужно делать DB query
    если сессия уже отозвана.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "test_session_order"
    request = create_mock_request(token=token, session_id=session_id)

    call_order = []

    async def mock_validate(sid, expected_user_id=None):
        call_order.append("validate_session")
        assert expected_user_id == str(test_user.id)
        return valid_session_data

    async def mock_execute(*args, **kwargs):
        call_order.append("db_execute")
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=test_user)
        return mock_result

    mock_db_session.execute = mock_execute

    with patch("app.api.deps.session_service.validate_session", side_effect=mock_validate):
        # Act
        await get_current_user(request, mock_db_session)

        # Assert
        assert call_order == ["validate_session", "db_execute"]


@pytest.mark.asyncio
async def test_get_current_user_with_impersonation_session(test_user, mock_db_session):
    """
    Тест: Сессия с флагом is_impersonation работает корректно.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "impersonation_session_123"
    request = create_mock_request(token=token, session_id=session_id)

    impersonation_session_data = {
        "user_id": str(test_user.id),
        "created_at": datetime.now(UTC).isoformat(),
        "is_impersonation": True,
    }

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=test_user)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = impersonation_session_data

        # Act
        user = await get_current_user(request, mock_db_session)

        # Assert
        assert user.id == test_user.id


@pytest.mark.asyncio
async def test_get_current_user_inactive_user_with_valid_session(test_user, mock_db_session, valid_session_data):
    """
    Тест: Даже с валидной сессией, неактивный пользователь получает 401.
    """
    # Arrange
    test_user.is_active = False
    token = create_jwt_token(test_user.id)
    session_id = "valid_session_inactive_user"
    request = create_mock_request(token=token, session_id=session_id)

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=test_user)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = valid_session_data

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, mock_db_session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User account is inactive"
        assert request.state.auth_error_reason == "user_inactive"


# ============================================================================
# Tests: Edge cases
# ============================================================================


@pytest.mark.asyncio
async def test_validate_session_rejects_owner_mismatch(caplog):
    """
    Тест: validate_session отклоняет session, если владелец не совпадает с JWT subject.
    """
    import logging

    caplog.set_level(logging.WARNING)

    session_id = "mismatch_session"
    expected_user_id = uuid4()
    actual_user_id = uuid4()
    redis = AsyncMock()
    redis.get.return_value = json.dumps(
        {
            "user_id": str(actual_user_id),
            "created_at": datetime.now(UTC).isoformat(),
            "is_impersonation": False,
        }
    )

    with patch("app.services.session_service.get_redis", new=AsyncMock(return_value=redis)):
        session_data = await session_service.validate_session(session_id, expected_user_id=str(expected_user_id))

    assert session_data is None
    assert "owner mismatch" in caplog.text


@pytest.mark.asyncio
async def test_get_current_user_with_very_long_session_id(test_user, mock_db_session, valid_session_data):
    """
    Тест: Очень длинный session_id обрабатывается корректно.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "x" * 1000  # Очень длинный ID
    request = create_mock_request(token=token, session_id=session_id)

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=test_user)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = valid_session_data

        # Act
        user = await get_current_user(request, mock_db_session)

        # Assert
        assert user.id == test_user.id
        mock_validate.assert_called_once_with(session_id, expected_user_id=str(test_user.id))


@pytest.mark.asyncio
async def test_get_current_user_multiple_calls_same_session(test_user, mock_db_session, valid_session_data):
    """
    Тест: Множественные вызовы с одной сессией работают корректно.
    """
    # Arrange
    token = create_jwt_token(test_user.id)
    session_id = "reused_session_123"

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=test_user)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.deps.session_service.validate_session", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = valid_session_data

        # Act - вызываем 3 раза
        for _ in range(3):
            request = create_mock_request(token=token, session_id=session_id)
            user = await get_current_user(request, mock_db_session)
            assert user.id == test_user.id

        # Assert - validate_session вызвана 3 раза
        assert mock_validate.call_count == 3
