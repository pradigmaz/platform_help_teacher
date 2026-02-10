"""
Suspicion detection system.
Компонентный fingerprint matching, timing correlation, антидетект detection.
"""
from .constants import (
    SCORE_CANVAS,
    SCORE_IP,
    SCORE_PLATFORM,
    SCORE_SCREEN,
    SCORE_TIMING,
    SCORE_UA_BROWSER,
    SCORE_UA_OS,
    SCORE_WEBGL,
    THRESHOLD_HIGH,
    THRESHOLD_PROBABLE,
    TIMING_WINDOW_MINUTES,
)
from .fingerprint import (
    calculate_fingerprint_score,
    detect_inconsistencies,
    extract_platform_key,
    extract_screen_key,
    extract_webgl_key,
)
from .models import SuspicionMatch
from .scoring import get_confidence_level
from .service import (
    enrich_logs_with_suspicion,
    find_suspicion_for_anonymous,
    find_timing_correlation,
)
from .user_agent import parse_user_agent

__all__ = [
    "SuspicionMatch",
    "find_timing_correlation",
    "find_suspicion_for_anonymous",
    "enrich_logs_with_suspicion",
    "calculate_fingerprint_score",
    "detect_inconsistencies",
    "get_confidence_level",
]
