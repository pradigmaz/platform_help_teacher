"""
Rate Limit Warning System.

Мягкая система предупреждений вместо жёсткого бана.
"""
from .service import RateLimitService, get_rate_limit_service
from .constants import WarningLevel, THRESHOLDS

__all__ = [
    "RateLimitService",
    "get_rate_limit_service",
    "WarningLevel",
    "THRESHOLDS",
]
