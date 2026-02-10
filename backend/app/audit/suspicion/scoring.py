"""Scoring utilities для suspicion detection."""
from .constants import THRESHOLD_HIGH, THRESHOLD_PROBABLE


def get_confidence_level(score: int) -> str:
    """Определить уровень уверенности по score."""
    if score >= THRESHOLD_HIGH:
        return "high"
    elif score >= THRESHOLD_PROBABLE:
        return "probable"
    elif score > 0:
        return "low"
    return "none"
