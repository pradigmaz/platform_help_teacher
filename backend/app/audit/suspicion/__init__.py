"""
Suspicion detection system.
Компонентный fingerprint matching, timing correlation, антидетект detection.
"""
from .models import SuspicionMatch
from .constants import (
    SCORE_WEBGL, SCORE_SCREEN, SCORE_PLATFORM, SCORE_CANVAS,
    SCORE_IP, SCORE_UA_BROWSER, SCORE_UA_OS, SCORE_TIMING,
    THRESHOLD_PROBABLE, THRESHOLD_HIGH, TIMING_WINDOW_MINUTES,
)
from .fingerprint import (
    extract_webgl_key, extract_screen_key, extract_platform_key,
    calculate_fingerprint_score, detect_inconsistencies,
)
from .user_agent import parse_user_agent
from .scoring import get_confidence_level
from .service import (
    find_timing_correlation,
    find_suspicion_for_anonymous,
    enrich_logs_with_suspicion,
)

__all__ = [
    "SuspicionMatch",
    "find_timing_correlation",
    "find_suspicion_for_anonymous",
    "enrich_logs_with_suspicion",
    "calculate_fingerprint_score",
    "detect_inconsistencies",
    "get_confidence_level",
]
