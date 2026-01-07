"""
Калькулятор баллов за посещаемость.
"""
from typing import List

from app.models.attestation_settings import AttestationSettings
from app.models.attendance import Attendance, AttendanceStatus

from .models import AttendanceScoreResult


class AttendanceScoreCalculator:
    """Калькулятор баллов за посещаемость."""
    
    def calculate(
        self,
        attendance_records: List[Attendance],
        settings: AttestationSettings
    ) -> AttendanceScoreResult:
        """
        Расчёт баллов за посещаемость.
        
        Requirements:
        - 3.2: points for PRESENT status
        - 3.3: points for LATE status
        - 3.4: points for EXCUSED status
        - 3.5: points for ABSENT status
        - 3.7: multiply by attendance weight percentage
        """
        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0
        
        raw_score = 0.0
        
        for record in attendance_records:
            if record.status == AttendanceStatus.PRESENT:
                present_count += 1
                raw_score += settings.present_points
            elif record.status == AttendanceStatus.LATE:
                late_count += 1
                raw_score += settings.late_points
            elif record.status == AttendanceStatus.EXCUSED:
                excused_count += 1
                raw_score += settings.excused_points
            elif record.status == AttendanceStatus.ABSENT:
                absent_count += 1
                raw_score += settings.absent_points
        
        total_classes = len(attendance_records)
        
        # Нормализуем балл
        if total_classes > 0:
            max_attendance_score = total_classes * settings.present_points
            if max_attendance_score > 0:
                normalized_score = (raw_score / max_attendance_score) * 100
                normalized_score = max(0, normalized_score)
            else:
                normalized_score = 0
        else:
            normalized_score = 0
        
        # Взвешенный балл
        max_points = AttestationSettings.get_max_points(settings.attestation_type)
        weighted_score = (normalized_score * settings.attendance_weight / 100) * (max_points / 100)
        
        return AttendanceScoreResult(
            raw_score=raw_score,
            weighted_score=weighted_score,
            total_classes=total_classes,
            present_count=present_count,
            late_count=late_count,
            excused_count=excused_count,
            absent_count=absent_count
        )
