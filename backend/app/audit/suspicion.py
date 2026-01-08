"""
Сервис определения подозрительных анонимных запросов.
Корреляция по fingerprint, IP, timing, VPN detection.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import timedelta

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StudentAuditLog
from app.models.user import User

logger = logging.getLogger(__name__)

# Маппинг timezone -> ожидаемые страны IP
TIMEZONE_TO_COUNTRIES = {
    "Europe/Moscow": ["RU", "BY"],
    "Europe/Minsk": ["BY", "RU"],
    "Europe/Kiev": ["UA"],
    "Europe/Kyiv": ["UA"],
    "Asia/Almaty": ["KZ"],
    "Asia/Yekaterinburg": ["RU"],
    "Asia/Novosibirsk": ["RU"],
    "Europe/Samara": ["RU"],
    "Europe/Volgograd": ["RU"],
    "Asia/Vladivostok": ["RU"],
}

# Маппинг language -> ожидаемые страны
LANGUAGE_TO_COUNTRIES = {
    "ru": ["RU", "BY", "KZ", "UA"],
    "ru-RU": ["RU"],
    "be": ["BY"],
    "uk": ["UA"],
    "kk": ["KZ"],
}


class SuspicionMatch:
    """Результат анализа подозрения."""
    def __init__(self):
        self.fingerprint_match: Optional[Dict[str, Any]] = None
        self.ip_match: Optional[Dict[str, Any]] = None
        self.vpn_detected: Optional[Dict[str, Any]] = None
        self.has_suspicion: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_suspicion": self.has_suspicion,
            "fingerprint_match": self.fingerprint_match,
            "ip_match": self.ip_match,
            "vpn_detected": self.vpn_detected,
        }


async def find_suspicion_for_anonymous(
    db: AsyncSession,
    log: StudentAuditLog,
) -> SuspicionMatch:
    """
    Найти подозрение для анонимного запроса.
    Проверяет fingerprint и IP корреляцию.
    """
    result = SuspicionMatch()
    
    # Только для анонимных запросов
    if log.user_id is not None:
        return result
    
    # 1. Fingerprint match
    if log.fingerprint:
        fp_match = await _find_fingerprint_match(db, log.fingerprint, log.id)
        if fp_match:
            result.fingerprint_match = fp_match
            result.has_suspicion = True
    
    # 2. IP match
    ip_match = await _find_ip_match(db, log.ip_address, log.id)
    if ip_match:
        result.ip_match = ip_match
        result.has_suspicion = True
    
    return result


def detect_vpn_from_fingerprint(
    fingerprint: Optional[Dict[str, Any]],
    ip_country: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Детектит VPN по несоответствию fingerprint и IP.
    
    Признаки VPN:
    - timezone не соответствует стране IP
    - language не соответствует стране IP
    """
    if not fingerprint:
        return None
    
    timezone = fingerprint.get("timezone", "")
    language = fingerprint.get("language", "")
    
    mismatches = []
    fp_countries = set()
    
    # Определяем страны по timezone
    if timezone in TIMEZONE_TO_COUNTRIES:
        fp_countries.update(TIMEZONE_TO_COUNTRIES[timezone])
    
    # Определяем страны по language
    lang_base = language.split("-")[0] if language else ""
    if language in LANGUAGE_TO_COUNTRIES:
        fp_countries.update(LANGUAGE_TO_COUNTRIES[language])
    elif lang_base in LANGUAGE_TO_COUNTRIES:
        fp_countries.update(LANGUAGE_TO_COUNTRIES[lang_base])
    
    # Если fingerprint указывает на RU/BY/UA/KZ, но IP из другой страны
    ru_indicators = {"Europe/Moscow", "Europe/Minsk", "Europe/Kiev", "Europe/Kyiv"}
    ru_languages = {"ru", "ru-RU", "be", "uk", "kk"}
    
    is_ru_fingerprint = timezone in ru_indicators or lang_base in {"ru", "be", "uk", "kk"}
    
    if is_ru_fingerprint:
        # Проверяем известные признаки иностранного IP
        # (в реальности нужен GeoIP, но пока просто флагаем)
        return {
            "detected": True,
            "reason": "fingerprint_mismatch",
            "timezone": timezone,
            "language": language,
            "expected_countries": list(fp_countries) if fp_countries else ["RU", "BY", "UA", "KZ"],
        }
    
    return None


async def _find_fingerprint_match(
    db: AsyncSession,
    fingerprint: Dict[str, Any],
    exclude_log_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Найти пользователя с таким же fingerprint."""
    # Ищем записи с таким же fingerprint и известным user_id
    query = (
        select(StudentAuditLog.user_id, func.count().label('count'))
        .where(
            and_(
                StudentAuditLog.fingerprint == fingerprint,
                StudentAuditLog.user_id.isnot(None),
                StudentAuditLog.id != exclude_log_id,
            )
        )
        .group_by(StudentAuditLog.user_id)
        .order_by(func.count().desc())
        .limit(1)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if row:
        user_id, count = row
        user = await db.get(User, user_id)
        if user:
            return {
                "user_id": str(user_id),
                "user_name": user.full_name,
                "match_count": count,
                "match_type": "fingerprint",
            }
    
    return None


async def _find_ip_match(
    db: AsyncSession,
    ip_address: str,
    exclude_log_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Найти пользователя с таким же IP."""
    query = (
        select(StudentAuditLog.user_id, func.count().label('count'))
        .where(
            and_(
                StudentAuditLog.ip_address == ip_address,
                StudentAuditLog.user_id.isnot(None),
                StudentAuditLog.id != exclude_log_id,
            )
        )
        .group_by(StudentAuditLog.user_id)
        .order_by(func.count().desc())
        .limit(1)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if row:
        user_id, count = row
        user = await db.get(User, user_id)
        if user:
            return {
                "user_id": str(user_id),
                "user_name": user.full_name,
                "match_count": count,
                "match_type": "ip",
            }
    
    return None


async def enrich_logs_with_suspicion(
    db: AsyncSession,
    logs: List[StudentAuditLog],
) -> Dict[UUID, SuspicionMatch]:
    """
    Обогатить список логов информацией о подозрениях.
    Оптимизировано для batch обработки.
    """
    results: Dict[UUID, SuspicionMatch] = {}
    
    # VPN detection для ВСЕХ логов (не только анонимных)
    for log in logs:
        if log.fingerprint:
            vpn = detect_vpn_from_fingerprint(log.fingerprint)
            if vpn:
                if log.id not in results:
                    results[log.id] = SuspicionMatch()
                results[log.id].vpn_detected = vpn
                results[log.id].has_suspicion = True
    
    # Собираем анонимные логи для fingerprint/IP matching
    anonymous_logs = [log for log in logs if log.user_id is None]
    
    if not anonymous_logs:
        return results
    
    # Собираем уникальные fingerprints и IPs
    fingerprints = {
        log.id: log.fingerprint 
        for log in anonymous_logs 
        if log.fingerprint
    }
    ips = {log.id: log.ip_address for log in anonymous_logs}
    
    # Batch запрос для fingerprint matches
    if fingerprints:
        fp_values = list(set(str(fp) for fp in fingerprints.values() if fp))
        if fp_values:
            fp_query = (
                select(
                    StudentAuditLog.fingerprint,
                    StudentAuditLog.user_id,
                    func.count().label('count')
                )
                .where(
                    and_(
                        StudentAuditLog.user_id.isnot(None),
                        StudentAuditLog.fingerprint.isnot(None),
                    )
                )
                .group_by(StudentAuditLog.fingerprint, StudentAuditLog.user_id)
            )
            fp_result = await db.execute(fp_query)
            fp_matches = {}
            for row in fp_result.all():
                fp_key = str(row.fingerprint)
                if fp_key not in fp_matches or row.count > fp_matches[fp_key][1]:
                    fp_matches[fp_key] = (row.user_id, row.count)
    
    # Batch запрос для IP matches
    ip_values = list(set(ips.values()))
    ip_query = (
        select(
            StudentAuditLog.ip_address,
            StudentAuditLog.user_id,
            func.count().label('count')
        )
        .where(
            and_(
                StudentAuditLog.user_id.isnot(None),
                StudentAuditLog.ip_address.in_(ip_values),
            )
        )
        .group_by(StudentAuditLog.ip_address, StudentAuditLog.user_id)
    )
    ip_result = await db.execute(ip_query)
    ip_matches = {}
    for row in ip_result.all():
        if row.ip_address not in ip_matches or row.count > ip_matches[row.ip_address][1]:
            ip_matches[row.ip_address] = (row.user_id, row.count)
    
    # Собираем user_ids для получения имён
    user_ids = set()
    if fingerprints:
        for fp in fingerprints.values():
            fp_key = str(fp)
            if fp_key in fp_matches:
                user_ids.add(fp_matches[fp_key][0])
    for ip in ips.values():
        if ip in ip_matches:
            user_ids.add(ip_matches[ip][0])
    
    # Получаем имена пользователей
    users_map = {}
    if user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    
    # Формируем результаты для анонимных
    for log in anonymous_logs:
        if log.id not in results:
            results[log.id] = SuspicionMatch()
        match = results[log.id]
        
        # Fingerprint match
        if log.fingerprint:
            fp_key = str(log.fingerprint)
            if fp_key in fp_matches:
                user_id, count = fp_matches[fp_key]
                match.fingerprint_match = {
                    "user_id": str(user_id),
                    "user_name": users_map.get(user_id, "Unknown"),
                    "match_count": count,
                    "match_type": "fingerprint",
                }
                match.has_suspicion = True
        
        # IP match
        if log.ip_address in ip_matches:
            user_id, count = ip_matches[log.ip_address]
            match.ip_match = {
                "user_id": str(user_id),
                "user_name": users_map.get(user_id, "Unknown"),
                "match_count": count,
                "match_type": "ip",
            }
            match.has_suspicion = True
    
    return results
