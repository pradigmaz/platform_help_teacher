"""
Security Detector — детекция атак и управление страйками.
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any, Set
from uuid import UUID

from app.core.redis import get_redis

from .constants import (
    AttackType, StrikeLevel, AttackPattern, ATTACK_PATTERNS,
    REDIS_STRIKE_COUNT, REDIS_STRIKE_DETAILS, REDIS_SECURITY_BAN,
    STRIKE_WINDOW, BAN_DURATION, MAX_STRIKES, MESSAGES
)

logger = logging.getLogger(__name__)

_detector: Optional["SecurityDetector"] = None

# Redis keys для fingerprint
REDIS_USER_FINGERPRINTS = "sec:fp:user:{user_id}"  # Set fingerprints пользователя
REDIS_FINGERPRINT_BAN = "sec:ban:fp:{fp_hash}"  # Бан по fingerprint
REDIS_COMPONENT_BAN = "sec:ban:comp:{comp_hash}"  # Бан по компоненту fingerprint

# Компоненты fingerprint для отдельного бана (уникальные идентификаторы устройства)
# ВАЖНО: audio и screen убраны — слишком много коллизий между пользователями
BANNABLE_COMPONENTS = [
    "webgl",       # GPU renderer — уникален для видеокарты
    "canvas",      # Canvas fingerprint — уникален для браузера+GPU
    # "audio",     # ОТКЛЮЧЕНО: слишком много коллизий, банит невинных
    # "screen",    # ОТКЛЮЧЕНО: разрешение экрана не уникально
]


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
        message: Optional[str] = None,
        ban_until: Optional[datetime] = None,
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
    
    def _hash_fingerprint(self, fingerprint: Dict[str, Any]) -> str:
        """Хеширует fingerprint для использования как ключ."""
        fp_str = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(fp_str.encode()).hexdigest()[:16]
    
    def _extract_component_hashes(self, fingerprint: Dict[str, Any]) -> Dict[str, str]:
        """Извлекает хеши отдельных компонентов fingerprint."""
        hashes = {}
        for comp in BANNABLE_COMPONENTS:
            if comp in fingerprint and fingerprint[comp]:
                comp_str = json.dumps(fingerprint[comp], sort_keys=True)
                hashes[comp] = hashlib.sha256(comp_str.encode()).hexdigest()[:16]
        return hashes
    
    def detect_attack(self, url: str, body: Optional[str] = None) -> Optional[AttackPattern]:
        """
        Проверяет URL и тело запроса на паттерны атак.
        
        Returns:
            AttackPattern если найдено совпадение, иначе None
        """
        # Проверяем URL
        for pattern in ATTACK_PATTERNS:
            if pattern.pattern.search(url):
                return pattern
        
        # Проверяем тело (если есть)
        if body:
            for pattern in ATTACK_PATTERNS:
                if pattern.pattern.search(body):
                    return pattern
        
        return None
    
    async def check_and_record(
        self,
        ip_address: str,
        url: str,
        user_id: Optional[UUID] = None,
        body: Optional[str] = None,
        response_status: Optional[int] = None,
        fingerprint: Optional[Dict[str, Any]] = None,
    ) -> DetectionResult:
        """
        Проверяет запрос и записывает страйк если нужно.
        
        Args:
            ip_address: IP клиента
            url: URL запроса
            user_id: ID пользователя (если авторизован)
            body: Тело запроса
            response_status: Код ответа (для детекции IDOR по 404)
            fingerprint: Отпечаток браузера
        
        Returns:
            DetectionResult с информацией о детекции и страйках
        """
        redis = await get_redis()
        if not redis:
            return DetectionResult()
        
        identifier = f"user:{user_id}" if user_id else f"ip:{ip_address}"
        fp_hash = self._hash_fingerprint(fingerprint) if fingerprint else None
        
        # Проверяем бан по user/ip
        ban_key = REDIS_SECURITY_BAN.format(identifier=identifier)
        if await redis.exists(ban_key):
            ttl = await redis.ttl(ban_key)
            return DetectionResult(
                is_suspicious=True,
                strike_level=StrikeLevel.BANNED,
                message=MESSAGES[StrikeLevel.BANNED],
                ban_until=datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None,
            )
        
        # Проверяем бан по fingerprint
        if fp_hash:
            fp_ban_key = REDIS_FINGERPRINT_BAN.format(fp_hash=fp_hash)
            if await redis.exists(fp_ban_key):
                ttl = await redis.ttl(fp_ban_key)
                logger.warning(f"🚫 FINGERPRINT BAN: fp={fp_hash} | identifier={identifier}")
                return DetectionResult(
                    is_suspicious=True,
                    strike_level=StrikeLevel.BANNED,
                    message=MESSAGES[StrikeLevel.BANNED],
                    ban_until=datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None,
                )
        
        # Проверяем бан по компонентам fingerprint (webgl, canvas, audio, screen)
        if fingerprint:
            comp_hashes = self._extract_component_hashes(fingerprint)
            for comp_name, comp_hash in comp_hashes.items():
                comp_ban_key = REDIS_COMPONENT_BAN.format(comp_hash=f"{comp_name}:{comp_hash}")
                if await redis.exists(comp_ban_key):
                    ttl = await redis.ttl(comp_ban_key)
                    logger.warning(
                        f"🚫 COMPONENT BAN: {comp_name}={comp_hash} | identifier={identifier}"
                    )
                    return DetectionResult(
                        is_suspicious=True,
                        strike_level=StrikeLevel.BANNED,
                        message=MESSAGES[StrikeLevel.BANNED],
                        ban_until=datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None,
                    )
            
            # Сохраняем fingerprint и компоненты пользователя для будущих банов
            if user_id and fp_hash:
                fp_set_key = REDIS_USER_FINGERPRINTS.format(user_id=user_id)
                # Сохраняем полный fingerprint hash
                await redis.sadd(fp_set_key, f"fp:{fp_hash}")
                # Сохраняем компоненты
                for comp_name, comp_hash in comp_hashes.items():
                    await redis.sadd(fp_set_key, f"{comp_name}:{comp_hash}")
                await redis.expire(fp_set_key, 86400 * 30)  # 30 дней
        
        # Детектим атаку по паттернам
        attack = self.detect_attack(url, body)
        
        # Детектим IDOR по 404 на UUID-ресурсах
        if not attack and response_status == 404:
            if self._looks_like_idor(url):
                attack = AttackPattern(
                    pattern=None,  # type: ignore
                    attack_type=AttackType.IDOR,
                    description="Possible IDOR: 404 on UUID resource",
                    severity=1
                )
        
        if not attack:
            return DetectionResult()
        
        # Записываем страйк
        return await self._record_strike(
            redis, identifier, ip_address, user_id, url, attack, fp_hash, fingerprint
        )
    
    def _looks_like_idor(self, url: str) -> bool:
        """Проверяет, похож ли URL на попытку IDOR."""
        import re
        # UUID в URL + не публичный эндпоинт
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        if re.search(uuid_pattern, url, re.IGNORECASE):
            # Исключаем публичные эндпоинты
            public_paths = ["/public/", "/lectures/", "/report/"]
            if not any(p in url for p in public_paths):
                return True
        return False
    
    async def _record_strike(
        self,
        redis,
        identifier: str,
        ip_address: str,
        user_id: Optional[UUID],
        url: str,
        attack: AttackPattern,
        fp_hash: Optional[str] = None,
        fingerprint: Optional[Dict[str, Any]] = None,
    ) -> DetectionResult:
        """Записывает страйк и возвращает результат."""
        count_key = REDIS_STRIKE_COUNT.format(identifier=identifier)
        details_key = REDIS_STRIKE_DETAILS.format(identifier=identifier)
        
        # Инкрементируем счётчик (с учётом severity)
        increment = attack.severity if hasattr(attack, 'severity') else 1
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
            "severity": getattr(attack, 'severity', 1),
        }
        await redis.rpush(details_key, json.dumps(detail))
        
        # Определяем уровень
        if count >= MAX_STRIKES:
            level = StrikeLevel.BANNED
            # Устанавливаем бан по user/ip
            ban_key = REDIS_SECURITY_BAN.format(identifier=identifier)
            await redis.setex(ban_key, BAN_DURATION, attack.attack_type.value)
            ban_until = datetime.utcnow() + timedelta(seconds=BAN_DURATION)
            
            # SECURITY: Баним все fingerprints пользователя
            if user_id:
                await self._ban_user_fingerprints(redis, user_id)
            
            # Баним текущий fingerprint
            if fp_hash:
                fp_ban_key = REDIS_FINGERPRINT_BAN.format(fp_hash=fp_hash)
                await redis.setex(fp_ban_key, BAN_DURATION, str(user_id or ip_address))
            
            # Баним компоненты текущего fingerprint
            if fingerprint:
                comp_hashes = self._extract_component_hashes(fingerprint)
                for comp_name, comp_hash in comp_hashes.items():
                    comp_ban_key = REDIS_COMPONENT_BAN.format(comp_hash=f"{comp_name}:{comp_hash}")
                    await redis.setex(comp_ban_key, BAN_DURATION, str(user_id or ip_address))
            
            logger.warning(
                f"🚫 SECURITY BAN: {identifier} | "
                f"attack={attack.attack_type.value} | url={url[:100]} | fp={fp_hash}"
            )
        elif count >= 2:
            level = StrikeLevel.RECORDED
            ban_until = None
            logger.warning(
                f"⚠️ SECURITY STRIKE {count}/{MAX_STRIKES}: {identifier} | "
                f"attack={attack.attack_type.value} | url={url[:100]}"
            )
        else:
            level = StrikeLevel.WARNING
            ban_until = None
            logger.info(
                f"⚠️ SECURITY WARNING: {identifier} | "
                f"attack={attack.attack_type.value} | url={url[:100]}"
            )
        
        return DetectionResult(
            is_suspicious=True,
            attack_type=attack.attack_type,
            description=attack.description,
            strike_level=level,
            strike_count=count,
            message=MESSAGES.get(level),
            ban_until=ban_until,
        )
    
    async def _ban_user_fingerprints(self, redis, user_id: UUID) -> int:
        """Банит все известные fingerprints и компоненты пользователя."""
        fp_set_key = REDIS_USER_FINGERPRINTS.format(user_id=user_id)
        identifiers = await redis.smembers(fp_set_key)
        
        banned_count = 0
        for identifier in identifiers:
            if identifier.startswith("fp:"):
                # Полный fingerprint hash
                fp_hash = identifier[3:]
                fp_ban_key = REDIS_FINGERPRINT_BAN.format(fp_hash=fp_hash)
                await redis.setex(fp_ban_key, BAN_DURATION, str(user_id))
            else:
                # Компонент (webgl:hash, canvas:hash, etc.)
                comp_ban_key = REDIS_COMPONENT_BAN.format(comp_hash=identifier)
                await redis.setex(comp_ban_key, BAN_DURATION, str(user_id))
            banned_count += 1
        
        if banned_count > 0:
            logger.warning(
                f"🔒 Banned {banned_count} fingerprints/components for user {user_id}"
            )
        
        return banned_count
    
    async def get_strikes(self, identifier: str) -> Tuple[int, List[Dict[str, Any]]]:
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
        ban_key = REDIS_SECURITY_BAN.format(identifier=identifier)
        
        await redis.delete(count_key, details_key, ban_key)
        logger.info(f"Cleared security strikes for {identifier}")
        return True
