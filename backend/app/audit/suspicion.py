"""
Сервис определения подозрительных анонимных запросов.
Компонентный fingerprint matching, timing correlation, антидетект detection.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StudentAuditLog
from app.models.user import User

logger = logging.getLogger(__name__)

# Веса для scoring
SCORE_WEBGL = 40        # WebGL vendor+renderer — очень стабильный
SCORE_SCREEN = 25       # Screen resolution — стабильный  
SCORE_PLATFORM = 20     # Platform + cores — стабильный
SCORE_CANVAS = 15       # Canvas — может меняться
SCORE_IP = 30           # IP match
SCORE_UA_BROWSER = 15   # User-Agent browser match
SCORE_UA_OS = 10        # User-Agent OS match
SCORE_TIMING = 50       # Timing correlation (очень сильный сигнал)

THRESHOLD_PROBABLE = 50
THRESHOLD_HIGH = 70

# Timing window для correlation (минуты)
TIMING_WINDOW_MINUTES = 5


class SuspicionMatch:
    """Результат анализа подозрения."""
    def __init__(self):
        self.fingerprint_match: Optional[Dict[str, Any]] = None
        self.ip_match: Optional[Dict[str, Any]] = None
        self.timing_match: Optional[Dict[str, Any]] = None
        self.inconsistencies: List[str] = []
        self.component_matches: List[str] = []
        self.total_score: int = 0
        self.confidence: str = "none"
        self.has_suspicion: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "has_suspicion": self.has_suspicion,
            "score": self.total_score,
            "confidence": self.confidence,
        }
        if self.fingerprint_match:
            result["fingerprint_match"] = self.fingerprint_match
        if self.ip_match:
            result["ip_match"] = self.ip_match
        if self.timing_match:
            result["timing_match"] = self.timing_match
        if self.inconsistencies:
            result["inconsistencies"] = self.inconsistencies
        if self.component_matches:
            result["matched_components"] = self.component_matches
        return result


def _extract_webgl_key(fp: Dict[str, Any]) -> Optional[str]:
    """Извлечь ключ WebGL."""
    webgl = fp.get("webgl")
    if webgl and isinstance(webgl, dict):
        vendor = webgl.get("vendor", "")
        renderer = webgl.get("renderer", "")
        if vendor and renderer:
            return f"{vendor}|{renderer}"
    return None


def _extract_screen_key(fp: Dict[str, Any]) -> Optional[str]:
    """Извлечь ключ screen."""
    screen = fp.get("screen")
    if screen and isinstance(screen, dict):
        w = screen.get("width")
        h = screen.get("height")
        depth = screen.get("colorDepth")
        if w and h:
            return f"{w}x{h}x{depth or 24}"
    return None


def _extract_platform_key(fp: Dict[str, Any]) -> Optional[str]:
    """Извлечь ключ platform."""
    platform = fp.get("platform", "")
    cores = fp.get("hardwareConcurrency", 0)
    if platform:
        return f"{platform}|{cores}"
    return None


def _parse_user_agent(ua: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Извлечь browser и OS из User-Agent."""
    if not ua:
        return None, None
    
    ua_lower = ua.lower()
    
    browser = None
    if "edg/" in ua_lower:
        browser = "edge"
    elif "chrome/" in ua_lower and "safari/" in ua_lower:
        browser = "chrome"
    elif "firefox/" in ua_lower:
        browser = "firefox"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        browser = "safari"
    elif "opera" in ua_lower or "opr/" in ua_lower:
        browser = "opera"
    
    os_name = None
    if "windows" in ua_lower:
        os_name = "windows"
    elif "mac os" in ua_lower or "macos" in ua_lower:
        os_name = "macos"
    elif "android" in ua_lower:
        os_name = "android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "ios"
    elif "linux" in ua_lower:
        os_name = "linux"
    
    return browser, os_name


def detect_inconsistencies(fp: Dict[str, Any]) -> List[str]:
    """
    Детектит нереалистичные комбинации (признак антидетект браузера).
    """
    issues = []
    
    webgl = fp.get("webgl", {})
    renderer = webgl.get("renderer", "").lower() if webgl else ""
    cores = fp.get("hardwareConcurrency", 0)
    platform = fp.get("platform", "").lower()
    
    # Мощный GPU но мало ядер — подозрительно
    powerful_gpu_keywords = ["rtx", "gtx", "radeon rx", "nvidia", "geforce"]
    has_powerful_gpu = any(kw in renderer for kw in powerful_gpu_keywords)
    if has_powerful_gpu and cores and cores < 4:
        issues.append("powerful_gpu_low_cores")
    
    # Mac platform но Windows в renderer
    if "mac" in platform and "windows" in renderer:
        issues.append("platform_renderer_mismatch")
    
    # Linux platform но DirectX в renderer
    if "linux" in platform and ("d3d" in renderer or "direct" in renderer):
        issues.append("linux_directx_mismatch")
    
    # Очень старый GPU с новым браузером — может быть спуфинг
    old_gpu_keywords = ["intel hd 3000", "intel hd 4000", "geforce 8", "geforce 9"]
    has_old_gpu = any(kw in renderer for kw in old_gpu_keywords)
    if has_old_gpu and cores and cores >= 8:
        issues.append("old_gpu_many_cores")
    
    return issues


def calculate_fingerprint_score(
    fp1: Dict[str, Any],
    fp2: Dict[str, Any],
    ua1: Optional[str] = None,
    ua2: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Рассчитать score совпадения двух fingerprints."""
    score = 0
    matches = []
    
    # WebGL
    webgl1 = _extract_webgl_key(fp1)
    webgl2 = _extract_webgl_key(fp2)
    if webgl1 and webgl2 and webgl1 == webgl2:
        score += SCORE_WEBGL
        matches.append("webgl")
    
    # Screen
    screen1 = _extract_screen_key(fp1)
    screen2 = _extract_screen_key(fp2)
    if screen1 and screen2 and screen1 == screen2:
        score += SCORE_SCREEN
        matches.append("screen")
    
    # Platform
    platform1 = _extract_platform_key(fp1)
    platform2 = _extract_platform_key(fp2)
    if platform1 and platform2 and platform1 == platform2:
        score += SCORE_PLATFORM
        matches.append("platform")
    
    # Canvas
    canvas1 = fp1.get("canvas")
    canvas2 = fp2.get("canvas")
    if canvas1 and canvas2 and canvas1 == canvas2:
        score += SCORE_CANVAS
        matches.append("canvas")
    
    # User-Agent
    if ua1 and ua2:
        browser1, os1 = _parse_user_agent(ua1)
        browser2, os2 = _parse_user_agent(ua2)
        if browser1 and browser2 and browser1 == browser2:
            score += SCORE_UA_BROWSER
            matches.append("browser")
        if os1 and os2 and os1 == os2:
            score += SCORE_UA_OS
            matches.append("os")
    
    return score, matches


def get_confidence_level(score: int) -> str:
    if score >= THRESHOLD_HIGH:
        return "high"
    elif score >= THRESHOLD_PROBABLE:
        return "probable"
    elif score > 0:
        return "low"
    return "none"



async def find_timing_correlation(
    db: AsyncSession,
    log: StudentAuditLog,
) -> Optional[Dict[str, Any]]:
    """
    Найти авторизованные запросы в близком временном окне.
    Сильный сигнал: анонимный и авторизованный запрос с одного IP в пределах 5 минут.
    """
    if not log.created_at or not log.ip_address:
        return None
    
    time_from = log.created_at - timedelta(minutes=TIMING_WINDOW_MINUTES)
    time_to = log.created_at + timedelta(minutes=TIMING_WINDOW_MINUTES)
    
    query = (
        select(
            StudentAuditLog.user_id,
            StudentAuditLog.created_at,
            StudentAuditLog.path,
        )
        .where(
            and_(
                StudentAuditLog.user_id.isnot(None),
                StudentAuditLog.ip_address == log.ip_address,
                StudentAuditLog.created_at >= time_from,
                StudentAuditLog.created_at <= time_to,
                StudentAuditLog.id != log.id,
            )
        )
        .order_by(func.abs(func.extract('epoch', StudentAuditLog.created_at - log.created_at)))
        .limit(1)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if row:
        user = await db.get(User, row.user_id)
        time_diff = abs((row.created_at - log.created_at).total_seconds())
        return {
            "user_id": str(row.user_id),
            "user_name": user.full_name if user else "Unknown",
            "time_diff_seconds": int(time_diff),
            "auth_path": row.path,
            "match_type": "timing",
        }
    
    return None


async def find_suspicion_for_anonymous(
    db: AsyncSession,
    log: StudentAuditLog,
) -> SuspicionMatch:
    """
    Найти подозрение для анонимного запроса.
    Комбинирует: fingerprint matching, IP, timing correlation.
    """
    result = SuspicionMatch()
    
    if log.user_id is not None:
        return result
    
    # Inconsistencies в fingerprint
    if log.fingerprint:
        result.inconsistencies = detect_inconsistencies(log.fingerprint)
    
    candidates: Dict[UUID, Dict[str, Any]] = {}
    
    # 1. Timing correlation (самый сильный сигнал)
    timing = await find_timing_correlation(db, log)
    if timing:
        result.timing_match = timing
        result.total_score += SCORE_TIMING
        result.component_matches.append("timing")
        uid = UUID(timing["user_id"])
        candidates[uid] = {"name": timing["user_name"], "score": SCORE_TIMING}
    
    # 2. IP match
    if log.ip_address:
        ip_query = (
            select(StudentAuditLog.user_id, func.count().label('cnt'))
            .where(
                and_(
                    StudentAuditLog.ip_address == log.ip_address,
                    StudentAuditLog.user_id.isnot(None),
                    StudentAuditLog.id != log.id,
                )
            )
            .group_by(StudentAuditLog.user_id)
            .order_by(func.count().desc())
            .limit(3)
        )
        ip_result = await db.execute(ip_query)
        for row in ip_result.all():
            uid = row.user_id
            if uid not in candidates:
                candidates[uid] = {"score": 0}
            candidates[uid]["score"] += SCORE_IP
            candidates[uid]["ip_count"] = row.cnt
    
    # 3. Fingerprint component matching
    if log.fingerprint:
        webgl_key = _extract_webgl_key(log.fingerprint)
        screen_key = _extract_screen_key(log.fingerprint)
        
        if webgl_key or screen_key:
            fp_query = (
                select(
                    StudentAuditLog.user_id,
                    StudentAuditLog.fingerprint,
                    StudentAuditLog.user_agent,
                )
                .where(
                    and_(
                        StudentAuditLog.user_id.isnot(None),
                        StudentAuditLog.fingerprint.isnot(None),
                    )
                )
                .distinct(StudentAuditLog.user_id)
                .limit(100)
            )
            fp_result = await db.execute(fp_query)
            
            for row in fp_result.all():
                if not row.fingerprint:
                    continue
                
                score, matches = calculate_fingerprint_score(
                    log.fingerprint, row.fingerprint,
                    log.user_agent, row.user_agent
                )
                
                if score > 0:
                    uid = row.user_id
                    if uid not in candidates:
                        candidates[uid] = {"score": 0}
                    candidates[uid]["score"] += score
                    candidates[uid]["fp_matches"] = matches
    
    if not candidates:
        return result
    
    # Находим лучшего кандидата
    best_uid = max(candidates.keys(), key=lambda u: candidates[u]["score"])
    best = candidates[best_uid]
    
    # Получаем имя если нет
    if "name" not in best:
        user = await db.get(User, best_uid)
        best["name"] = user.full_name if user else "Unknown"
    
    result.total_score = best["score"]
    result.confidence = get_confidence_level(best["score"])
    
    if "ip_count" in best:
        result.ip_match = {
            "user_id": str(best_uid),
            "user_name": best["name"],
            "match_count": best["ip_count"],
            "match_type": "ip",
        }
        if "ip" not in result.component_matches:
            result.component_matches.append("ip")
    
    if "fp_matches" in best:
        result.component_matches.extend(best["fp_matches"])
    
    if result.confidence in ("probable", "high"):
        result.has_suspicion = True
        result.fingerprint_match = {
            "user_id": str(best_uid),
            "user_name": best["name"],
            "score": best["score"],
            "confidence": result.confidence,
            "matched_components": result.component_matches,
        }
    elif result.ip_match or result.timing_match:
        result.has_suspicion = True
    
    return result


async def enrich_logs_with_suspicion(
    db: AsyncSession,
    logs: List[StudentAuditLog],
) -> Dict[UUID, SuspicionMatch]:
    """
    Batch обогащение логов информацией о подозрениях.
    """
    results: Dict[UUID, SuspicionMatch] = {}
    
    anonymous_logs = [log for log in logs if log.user_id is None]
    if not anonymous_logs:
        return results
    
    # Собираем данные для batch processing
    all_ips = {log.ip_address for log in anonymous_logs if log.ip_address}
    
    # IP matches
    ip_user_map: Dict[str, Tuple[UUID, str, int]] = {}
    if all_ips:
        ip_query = (
            select(
                StudentAuditLog.ip_address,
                StudentAuditLog.user_id,
                func.count().label('cnt')
            )
            .where(
                and_(
                    StudentAuditLog.user_id.isnot(None),
                    StudentAuditLog.ip_address.in_(all_ips),
                )
            )
            .group_by(StudentAuditLog.ip_address, StudentAuditLog.user_id)
        )
        ip_result = await db.execute(ip_query)
        for row in ip_result.all():
            key = row.ip_address
            if key not in ip_user_map or row.cnt > ip_user_map[key][2]:
                ip_user_map[key] = (row.user_id, key, row.cnt)
    
    # Fingerprints авторизованных
    auth_fps: Dict[UUID, List[Tuple[Dict, Optional[str]]]] = {}
    fp_query = (
        select(
            StudentAuditLog.user_id,
            StudentAuditLog.fingerprint,
            StudentAuditLog.user_agent,
        )
        .where(
            and_(
                StudentAuditLog.user_id.isnot(None),
                StudentAuditLog.fingerprint.isnot(None),
            )
        )
        .distinct(StudentAuditLog.user_id, StudentAuditLog.fingerprint)
        .limit(200)
    )
    fp_result = await db.execute(fp_query)
    for row in fp_result.all():
        if row.user_id not in auth_fps:
            auth_fps[row.user_id] = []
        auth_fps[row.user_id].append((row.fingerprint, row.user_agent))
    
    # User names
    user_ids = set(ip_user_map[k][0] for k in ip_user_map)
    user_ids.update(auth_fps.keys())
    
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    
    # Process each anonymous log
    for log in anonymous_logs:
        match = SuspicionMatch()
        best_uid: Optional[UUID] = None
        best_score = 0
        matches: List[str] = []
        
        # Inconsistencies
        if log.fingerprint:
            match.inconsistencies = detect_inconsistencies(log.fingerprint)
        
        # IP
        if log.ip_address and log.ip_address in ip_user_map:
            uid, _, cnt = ip_user_map[log.ip_address]
            match.ip_match = {
                "user_id": str(uid),
                "user_name": users_map.get(uid, "Unknown"),
                "match_count": cnt,
                "match_type": "ip",
            }
            best_score += SCORE_IP
            matches.append("ip")
            best_uid = uid
            match.has_suspicion = True
        
        # Fingerprint
        if log.fingerprint:
            for uid, fps in auth_fps.items():
                for fp, ua in fps:
                    score, fp_matches = calculate_fingerprint_score(
                        log.fingerprint, fp, log.user_agent, ua
                    )
                    if score > 0:
                        total = score
                        combined = fp_matches.copy()
                        if best_uid == uid and "ip" in matches:
                            total += SCORE_IP
                            if "ip" not in combined:
                                combined.append("ip")
                        
                        if total > best_score:
                            best_score = total
                            matches = combined
                            best_uid = uid
        
        if best_score > 0:
            match.total_score = best_score
            match.confidence = get_confidence_level(best_score)
            match.component_matches = matches
            
            if match.confidence in ("probable", "high") and best_uid:
                match.has_suspicion = True
                match.fingerprint_match = {
                    "user_id": str(best_uid),
                    "user_name": users_map.get(best_uid, "Unknown"),
                    "score": best_score,
                    "confidence": match.confidence,
                    "matched_components": matches,
                }
        
        if match.has_suspicion or match.inconsistencies:
            results[log.id] = match
    
    return results
