"""
Security Detector — детекция атак и управление страйками.

АРХИТЕКТУРА БАНОВ:
- Бан по user_id — основной механизм
- Fingerprint → user_id mapping — для идентификации забаненного пользователя без JWT
- НЕ банить fingerprint глобально — это вызывает массовые баны в компьютерных классах
- IP бан — только как fallback для неавторизованных
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from app.core.redis import get_redis

from .constants import (
    ATTACK_PATTERNS,
    BAN_DURATION,
    MAX_STRIKES,
    MESSAGES,
    REDIS_STRIKE_COUNT,
    REDIS_STRIKE_DETAILS,
    STRIKE_WINDOW,
    AttackPattern,
    AttackType,
    StrikeLevel,
)

logger = logging.getLogger(__name__)

_detector: Optional["SecurityDetector"] = None

# Redis keys
REDIS_FP_TO_USER = "sec:fp_to_user:{fp_hash}"  # Mapping fingerprint → user_id (для идентификации)
REDIS_USER_BAN = "sec:ban:user:{user_id}"  # Бан пользователя
REDIS_IP_BAN = "sec:ban:ip:{ip}"  # Бан IP (fallback)
REDIS_USER_FINGERPRINTS = "sec:user_fps:{user_id}"  # Set fingerprints пользователя


def get_security_detector() -> "SecurityDetector":
    """Singleton детектора."""
    global _detector
    if _detector is None:
        _detector = SecurityDetector()
    return _detector


class DetectionResult:
    """Результат проверки запроса."""

    def __init__(
        self,
        is_suspicious: bool = False,
        attack_type: AttackType = AttackType.UNKNOWN,
        description: str = "",
        matched_pattern: str = "",
        strike_level: StrikeLevel = StrikeLevel.NONE,
        strike_count: int = 0,
        message: str | None = None,
        ban_until: datetime | None = None,
    ):
        self.is_suspicious = is_suspicious
        self.attack_type = attack_type
        self.description = description
        self.matched_pattern = matched_pattern
        self.strike_level = strike_level
        self.strike_count = strike_count
        self.message = message
        self.ban_until = ban_until


class SecurityDetector:
    """Детектор подозрительных запросов."""

    def _hash_fingerprint(self, fingerprint: dict[str, Any]) -> str:
        """Хеширует fingerprint для использования как ключ."""
        fp_str = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(fp_str.encode()).hexdigest()[:16]

    def detect_attack(self, url: str, body: str | None = None) -> AttackPattern | None:
        """
        Проверяет URL и тело запроса на паттерны атак.

        Returns:
            AttackPattern если найдено совпадение, иначе None
        """
        for pattern in ATTACK_PATTERNS:
            if pattern.pattern.search(url):
                return pattern

        if body:
            for pattern in ATTACK_PATTERNS:
                if pattern.pattern.search(body):
                    return pattern

        return None

    async def _get_user_by_fingerprint(self, redis, fp_hash: str) -> UUID | None:
        """Найти user_id по fingerprint (для идентификации без JWT)."""
        key = REDIS_FP_TO_USER.format(fp_hash=fp_hash)
        user_id_str = await redis.get(key)
        if user_id_str:
            try:
                return UUID(user_id_str)
            except ValueError:
                pass
        return None

    async def _is_user_banned(self, redis, user_id: UUID) -> tuple[bool, int | None]:
        """Проверить бан пользователя. Returns: (is_banned, ttl)"""
        key = REDIS_USER_BAN.format(user_id=user_id)
        if await redis.exists(key):
            ttl = await redis.ttl(key)
            return True, ttl
        return False, None

    async def _is_ip_banned(self, redis, ip: str) -> tuple[bool, int | None]:
        """Проверить бан IP. Returns: (is_banned, ttl)"""
        key = REDIS_IP_BAN.format(ip=ip)
        if await redis.exists(key):
            ttl = await redis.ttl(key)
            return True, ttl
        return False, None

    async def _save_fingerprint_mapping(self, redis, user_id: UUID, fp_hash: str) -> None:
        """Сохранить связь fingerprint → user_id для будущей идентификации."""
        # Mapping fp → user
        fp_key = REDIS_FP_TO_USER.format(fp_hash=fp_hash)
        await redis.setex(fp_key, 86400 * 30, str(user_id))  # 30 дней

        # Set fingerprints пользователя
        user_fps_key = REDIS_USER_FINGERPRINTS.format(user_id=user_id)
        await redis.sadd(user_fps_key, fp_hash)
        await redis.expire(user_fps_key, 86400 * 30)

    async def check_and_record(
        self,
        ip_address: str,
        url: str,
        user_id: UUID | None = None,
        body: str | None = None,
        response_status: int | None = None,
        fingerprint: dict[str, Any] | None = None,
    ) -> DetectionResult:
        """
        Проверяет запрос и записывает страйк если нужно.

        Логика проверки бана:
        1. Если есть user_id → проверить бан user
        2. Если нет user_id, но есть fingerprint → найти связанного user → проверить его бан
        3. Fallback: проверить бан IP
        """
        redis = await get_redis()
        if not redis:
            return DetectionResult()

        fp_hash = self._hash_fingerprint(fingerprint) if fingerprint else None
        effective_user_id = user_id

        # 1. Если есть user_id — проверяем его бан
        if user_id:
            is_banned, ttl = await self._is_user_banned(redis, user_id)
            if is_banned:
                return DetectionResult(
                    is_suspicious=True,
                    strike_level=StrikeLevel.BANNED,
                    message=MESSAGES[StrikeLevel.BANNED],
                    ban_until=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
                )
            # Сохраняем fingerprint → user mapping
            if fp_hash:
                await self._save_fingerprint_mapping(redis, user_id, fp_hash)

        # 2. Если нет user_id, но есть fingerprint — ищем связанного user
        elif fp_hash:
            linked_user_id = await self._get_user_by_fingerprint(redis, fp_hash)
            if linked_user_id:
                is_banned, ttl = await self._is_user_banned(redis, linked_user_id)
                if is_banned:
                    logger.warning(
                        f"🚫 Banned user detected by fingerprint: user={linked_user_id} fp={fp_hash} ip={ip_address}"
                    )
                    return DetectionResult(
                        is_suspicious=True,
                        strike_level=StrikeLevel.BANNED,
                        message=MESSAGES[StrikeLevel.BANNED],
                        ban_until=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
                    )
                effective_user_id = linked_user_id

        # 3. Fallback: проверяем бан IP (только для неавторизованных без fingerprint)
        if not user_id and not effective_user_id:
            is_banned, ttl = await self._is_ip_banned(redis, ip_address)
            if is_banned:
                return DetectionResult(
                    is_suspicious=True,
                    strike_level=StrikeLevel.BANNED,
                    message=MESSAGES[StrikeLevel.BANNED],
                    ban_until=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
                )

        # Определяем identifier для страйков
        identifier = f"user:{effective_user_id}" if effective_user_id else f"ip:{ip_address}"

        # Детектим атаку по паттернам
        attack = self.detect_attack(url, body)

        # Детектим IDOR по 404 на UUID-ресурсах
        if not attack and response_status == 404 and self._looks_like_idor(url):
            attack = AttackPattern(
                pattern=None,  # type: ignore
                attack_type=AttackType.IDOR,
                description="Possible IDOR: 404 on UUID resource",
                severity=1,
            )

        if not attack:
            return DetectionResult()

        # Записываем страйк
        return await self._record_strike(redis, identifier, ip_address, effective_user_id, url, attack, fp_hash)

    def _looks_like_idor(self, url: str) -> bool:
        """Проверяет, похож ли URL на попытку IDOR."""
        import re

        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        if re.search(uuid_pattern, url, re.IGNORECASE):
            public_paths = ["/public/", "/lectures/", "/report/"]
            if not any(p in url for p in public_paths):
                return True
        return False

    async def _record_strike(
        self,
        redis,
        identifier: str,
        ip_address: str,
        user_id: UUID | None,
        url: str,
        attack: AttackPattern,
        fp_hash: str | None = None,
    ) -> DetectionResult:
        """Записывает страйк и возвращает результат."""
        count_key = REDIS_STRIKE_COUNT.format(identifier=identifier)
        details_key = REDIS_STRIKE_DETAILS.format(identifier=identifier)

        # Инкрементируем счётчик (с учётом severity)
        increment = attack.severity if hasattr(attack, "severity") else 1
        count = await redis.incrby(count_key, increment)

        if count == increment:  # Первый страйк
            await redis.expire(count_key, STRIKE_WINDOW)
            await redis.expire(details_key, STRIKE_WINDOW)

        # Сохраняем детали
        detail = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": url[:500],
            "attack_type": attack.attack_type.value,
            "description": attack.description,
            "severity": getattr(attack, "severity", 1),
        }
        await redis.rpush(details_key, json.dumps(detail))

        # Определяем уровень
        if count >= MAX_STRIKES:
            level = StrikeLevel.BANNED
            ban_until = datetime.utcnow() + timedelta(seconds=BAN_DURATION)

            # Банить по user_id (основной механизм)
            if user_id:
                user_ban_key = REDIS_USER_BAN.format(user_id=user_id)
                await redis.setex(user_ban_key, BAN_DURATION, attack.attack_type.value)
                logger.warning(f"🚫 USER BAN: user={user_id} | attack={attack.attack_type.value} | url={url[:100]}")
            else:
                # Fallback: бан по IP для неавторизованных
                ip_ban_key = REDIS_IP_BAN.format(ip=ip_address)
                await redis.setex(ip_ban_key, BAN_DURATION, attack.attack_type.value)
                logger.warning(f"🚫 IP BAN: ip={ip_address} | attack={attack.attack_type.value} | url={url[:100]}")

        elif count >= 2:
            level = StrikeLevel.RECORDED
            ban_until = None
            logger.warning(
                f"⚠️ STRIKE {count}/{MAX_STRIKES}: {identifier} | attack={attack.attack_type.value} | url={url[:100]}"
            )
        else:
            level = StrikeLevel.WARNING
            ban_until = None
            logger.info(f"⚠️ WARNING: {identifier} | attack={attack.attack_type.value} | url={url[:100]}")

        return DetectionResult(
            is_suspicious=True,
            attack_type=attack.attack_type,
            description=attack.description,
            strike_level=level,
            strike_count=count,
            message=MESSAGES.get(level),
            ban_until=ban_until,
        )

    async def get_strikes(self, identifier: str) -> tuple[int, list[dict[str, Any]]]:
        """Получает текущие страйки для идентификатора."""
        redis = await get_redis()
        if not redis:
            return 0, []

        count_key = REDIS_STRIKE_COUNT.format(identifier=identifier)
        details_key = REDIS_STRIKE_DETAILS.format(identifier=identifier)

        count = await redis.get(count_key)
        details_raw = await redis.lrange(details_key, 0, -1)

        details = [json.loads(d) for d in details_raw] if details_raw else []

        return int(count or 0), details

    async def clear_strikes(self, identifier: str) -> bool:
        """Очищает страйки (для админа)."""
        redis = await get_redis()
        if not redis:
            return False

        count_key = REDIS_STRIKE_COUNT.format(identifier=identifier)
        details_key = REDIS_STRIKE_DETAILS.format(identifier=identifier)

        await redis.delete(count_key, details_key)
        logger.info(f"Cleared security strikes for {identifier}")
        return True

    async def unban_user(self, user_id: UUID) -> bool:
        """Разбанить пользователя (для админа)."""
        redis = await get_redis()
        if not redis:
            return False

        user_ban_key = REDIS_USER_BAN.format(user_id=user_id)
        await redis.delete(user_ban_key)

        # Очищаем страйки
        await self.clear_strikes(f"user:{user_id}")

        logger.info(f"Unbanned user {user_id}")
        return True

    async def unban_ip(self, ip: str) -> bool:
        """Разбанить IP (для админа)."""
        redis = await get_redis()
        if not redis:
            return False

        ip_ban_key = REDIS_IP_BAN.format(ip=ip)
        await redis.delete(ip_ban_key)

        # Очищаем страйки
        await self.clear_strikes(f"ip:{ip}")

        logger.info(f"Unbanned IP {ip}")
        return True
