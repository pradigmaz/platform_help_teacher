"""Основной сервис suspicion detection."""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import StudentAuditLog
from app.models.user import User

from .constants import SCORE_IP, SCORE_TIMING, TIMING_WINDOW_MINUTES
from .fingerprint import (
    calculate_fingerprint_score,
    detect_inconsistencies,
    extract_screen_key,
    extract_webgl_key,
)
from .models import SuspicionMatch
from .scoring import get_confidence_level

logger = logging.getLogger(__name__)


async def find_timing_correlation(
    db: AsyncSession,
    log: StudentAuditLog,
) -> dict[str, Any] | None:
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
        .order_by(func.abs(func.extract("epoch", StudentAuditLog.created_at - log.created_at)))
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

    candidates: dict[UUID, dict[str, Any]] = {}

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
            select(StudentAuditLog.user_id, func.count().label("cnt"))
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
        webgl_key = extract_webgl_key(log.fingerprint)
        screen_key = extract_screen_key(log.fingerprint)

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
                    log.fingerprint, row.fingerprint, log.user_agent, row.user_agent
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
    logs: list[StudentAuditLog],
) -> dict[UUID, SuspicionMatch]:
    """Batch обогащение логов информацией о подозрениях."""
    results: dict[UUID, SuspicionMatch] = {}

    anonymous_logs = [log for log in logs if log.user_id is None]
    if not anonymous_logs:
        return results

    # Собираем данные для batch processing
    all_ips = {log.ip_address for log in anonymous_logs if log.ip_address}

    # IP matches
    ip_user_map: dict[str, tuple[UUID, str, int]] = {}
    if all_ips:
        ip_query = (
            select(StudentAuditLog.ip_address, StudentAuditLog.user_id, func.count().label("cnt"))
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
    auth_fps: dict[UUID, list[tuple[dict, str | None]]] = {}
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
        best_uid: UUID | None = None
        best_score = 0
        matches: list[str] = []

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
                    score, fp_matches = calculate_fingerprint_score(log.fingerprint, fp, log.user_agent, ua)
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
