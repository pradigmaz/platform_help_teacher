"""
Rate Limit Warning System.

Мягкая система предупреждений вместо жёсткого бана.
"""
from .constants import THRESHOLDS, WarningLevel
from .service import RateLimitService, get_rate_limit_service

__all__ = [
    "RateLimitService",
    "get_rate_limit_service",
    "WarningLevel",
    "THRESHOLDS",
]
