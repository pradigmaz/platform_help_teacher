"""Модели данных для suspicion detection."""
from typing import Optional, Dict, Any, List


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
