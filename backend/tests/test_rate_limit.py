"""
Тесты для системы rate limit предупреждений.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.rate_limit.constants import (
    WarningLevel, THRESHOLDS, COUNT_WINDOW,
    REDIS_429_COUNT, REDIS_BAN
)
from app.services.rate_limit.service import RateLimitService


class TestRateLimitService:
    """Тесты RateLimitService."""
    
    @pytest.fixture
    def service(self):
        return RateLimitService()
    
    @pytest.fixture
    def mock_redis(self):
        """Мок Redis клиента."""
        redis = AsyncMock()
        redis.exists = AsyncMock(return_value=False)
        redis.get = AsyncMock(return_value=None)
        redis.incr = AsyncMock(return_value=1)
        redis.expire = AsyncMock()
        redis.setex = AsyncMock()
        redis.ttl = AsyncMock(return_value=600)
        return redis
    
    @pytest.mark.asyncio
    async def test_check_ban_not_banned(self, service, mock_redis):
        """Тест: пользователь не забанен."""
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            result = await service.check_ban("192.168.1.1")
            
            assert result.is_banned is False
            assert result.ban_until is None
    
    @pytest.mark.asyncio
    async def test_check_ban_ip_banned(self, service, mock_redis):
        """Тест: IP забанен."""
        mock_redis.exists = AsyncMock(return_value=False)
        mock_redis.get = AsyncMock(side_effect=lambda key: b"soft_ban" if "ban" in key else None)
        
        # Симулируем что бан существует
        async def mock_exists(key):
            return "ban" in key
        mock_redis.exists = mock_exists
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            result = await service.check_ban("192.168.1.1")
            
            assert result.is_banned is True
    
    @pytest.mark.asyncio
    async def test_record_violation_first_time(self, service, mock_redis):
        """Тест: первое нарушение — нет предупреждения."""
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.exists = AsyncMock(return_value=False)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1")
            
            assert level == WarningLevel.NONE
            assert message is None
    
    @pytest.mark.asyncio
    async def test_record_violation_soft_warning(self, service, mock_redis):
        """Тест: 10 нарушений — мягкое предупреждение."""
        soft_warning = next(t for t in THRESHOLDS if t.level == WarningLevel.SOFT_WARNING)
        mock_redis.incr = AsyncMock(return_value=soft_warning.count)
        mock_redis.exists = AsyncMock(return_value=False)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1")
            
            assert level == WarningLevel.SOFT_WARNING
            assert message is not None
            assert "много запросов" in message
    
    @pytest.mark.asyncio
    async def test_record_violation_soft_ban(self, service, mock_redis):
        """Тест: 50 нарушений — мягкий бан на 10 минут."""
        soft_ban = next(t for t in THRESHOLDS if t.level == WarningLevel.SOFT_BAN)
        mock_redis.incr = AsyncMock(return_value=soft_ban.count)
        mock_redis.exists = AsyncMock(return_value=False)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1")
            
            assert level == WarningLevel.SOFT_BAN
            assert message is not None
            # Проверяем что setex был вызван для бана
            mock_redis.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_violation_hard_ban(self, service, mock_redis):
        """Тест: 100 нарушений — жёсткий бан на 1 час."""
        hard_ban = next(t for t in THRESHOLDS if t.level == WarningLevel.HARD_BAN)
        mock_redis.incr = AsyncMock(return_value=hard_ban.count)
        mock_redis.exists = AsyncMock(return_value=False)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1")
            
            assert level == WarningLevel.HARD_BAN
            assert message is not None
            assert "1 час" in message
    
    @pytest.mark.asyncio
    async def test_record_violation_with_user_id(self, service, mock_redis):
        """Тест: нарушение с user_id использует user как идентификатор."""
        user_id = uuid4()
        mock_redis.incr = AsyncMock(return_value=50)
        mock_redis.exists = AsyncMock(return_value=False)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1", user_id=user_id)
            
            # Проверяем что использовался user_id в ключе
            incr_call = mock_redis.incr.call_args[0][0]
            assert str(user_id) in incr_call
    
    @pytest.mark.asyncio
    async def test_no_duplicate_warnings(self, service, mock_redis):
        """Тест: не отправляем повторные предупреждения."""
        mock_redis.incr = AsyncMock(return_value=10)
        # Предупреждение уже было отправлено
        mock_redis.exists = AsyncMock(return_value=True)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1")
            
            assert level == WarningLevel.SOFT_WARNING
            # Сообщение None потому что уже предупреждали
            assert message is None


class TestThresholds:
    """Тесты конфигурации порогов."""
    
    def test_thresholds_ordered(self):
        """Пороги должны быть в порядке возрастания."""
        counts = [t.count for t in THRESHOLDS]
        assert counts == sorted(counts)
    
    def test_soft_warning_no_ban(self):
        """Мягкое предупреждение не должно банить."""
        soft_warning = next(t for t in THRESHOLDS if t.level == WarningLevel.SOFT_WARNING)
        assert soft_warning.ban_duration == 0
        assert soft_warning.notify_admin is False
    
    def test_soft_ban_short_duration(self):
        """Мягкий бан должен быть коротким (10 мин)."""
        soft_ban = next(t for t in THRESHOLDS if t.level == WarningLevel.SOFT_BAN)
        assert soft_ban.ban_duration == 600  # 10 минут
        assert soft_ban.notify_admin is True
    
    def test_hard_ban_long_duration(self):
        """Жёсткий бан должен быть длинным (1 час)."""
        hard_ban = next(t for t in THRESHOLDS if t.level == WarningLevel.HARD_BAN)
        assert hard_ban.ban_duration == 3600  # 1 час
        assert hard_ban.notify_admin is True


class TestFingerprint:
    """Тесты работы с fingerprint."""
    
    def test_hash_fingerprint(self):
        """Тест хеширования fingerprint."""
        service = RateLimitService()
        
        fp1 = {"timezone": "Europe/Moscow", "language": "ru"}
        fp2 = {"timezone": "Europe/Moscow", "language": "ru"}
        fp3 = {"timezone": "Europe/London", "language": "en"}
        
        hash1 = service._hash_fingerprint(fp1)
        hash2 = service._hash_fingerprint(fp2)
        hash3 = service._hash_fingerprint(fp3)
        
        # Одинаковые fingerprint = одинаковый хеш
        assert hash1 == hash2
        # Разные fingerprint = разный хеш
        assert hash1 != hash3
        # Хеш короткий (16 символов)
        assert len(hash1) == 16


class TestAdminBypass:
    """Тесты обхода rate limit для админов."""
    
    @pytest.fixture
    def service(self):
        return RateLimitService()
    
    @pytest.fixture
    def mock_redis(self):
        """Мок Redis клиента."""
        redis = AsyncMock()
        redis.exists = AsyncMock(return_value=False)
        redis.get = AsyncMock(return_value=None)
        redis.incr = AsyncMock(return_value=100)
        redis.expire = AsyncMock()
        redis.setex = AsyncMock()
        redis.ttl = AsyncMock(return_value=600)
        return redis
    
    @pytest.mark.asyncio
    async def test_admin_bypass_check_ban(self, service, mock_redis):
        """Тест: админ не проверяется на бан."""
        from app.services.rate_limit import service as svc_module
        
        admin_id = uuid4()
        # Добавляем админа в кэш
        svc_module._admin_user_ids.add(admin_id)
        
        try:
            # Даже если IP забанен, админ проходит
            mock_redis.get = AsyncMock(return_value=b"hard_ban")
            
            with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
                result = await service.check_ban("192.168.1.1", user_id=admin_id)
                
                assert result.is_banned is False
        finally:
            svc_module._admin_user_ids.discard(admin_id)
    
    @pytest.mark.asyncio
    async def test_admin_bypass_record_violation(self, service, mock_redis):
        """Тест: нарушения админа не записываются."""
        from app.services.rate_limit import service as svc_module
        
        admin_id = uuid4()
        svc_module._admin_user_ids.add(admin_id)
        
        try:
            with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
                level, message = await service.record_violation("192.168.1.1", user_id=admin_id)
                
                assert level == WarningLevel.NONE
                assert message is None
                # Redis не должен вызываться
                mock_redis.incr.assert_not_called()
        finally:
            svc_module._admin_user_ids.discard(admin_id)
    
    @pytest.mark.asyncio
    async def test_non_admin_still_limited(self, service, mock_redis):
        """Тест: обычный пользователь всё ещё лимитируется."""
        from app.services.rate_limit import service as svc_module
        
        user_id = uuid4()
        # Убеждаемся что user_id не в кэше админов
        svc_module._admin_user_ids.discard(user_id)
        
        mock_redis.incr = AsyncMock(return_value=100)
        mock_redis.exists = AsyncMock(return_value=False)
        
        with patch('app.services.rate_limit.service.get_redis', return_value=mock_redis):
            level, message = await service.record_violation("192.168.1.1", user_id=user_id)
            
            assert level == WarningLevel.HARD_BAN
            assert message is not None
