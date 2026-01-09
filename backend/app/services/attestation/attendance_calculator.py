"""
Калькулятор баллов за посещаемость.
Автобалансировка: баллы = attendance_ratio * max_attendance_points

Посещаемость = процент от фактически прошедших занятий.
EXCUSED не учитывается (занятие как будто не было).
"""
from typing import List
from dataclasses import dataclass

from app.models.attestation_settings import AttestationSettings
from app.models.attendance import Attendance, AttendanceStatus


@dataclass
class AttendanceScoreResult:
    """Результат расчёта баллов за посещаемость"""
    score: float           # Итоговые баллы
    max_score: float       # Максимум возможных баллов
    ratio: float           # Процент посещаемости (0-1)
    total_classes: int     # Всего занятий
    counted_classes: int   # Учтённых занятий (без EXCUSED)
    present_count: int
    late_count: int
    excused_count: int
    absent_count: int


class AttendanceScoreCalculator:
    """Калькулятор баллов за посещаемость (автобалансировка)"""
    
    def calculate(
        self,
        attendance_records: List[Attendance],
        settings: AttestationSettings,
        transfer_attendance: dict = None
    ) -> AttendanceScoreResult:
        """
        Расчёт баллов за посещаемость.
        
        Формула:
        - max_attendance = attestation_max * (attendance_weight / 100)
        - attendance_ratio = (present + late * late_coef) / counted_classes
        - score = attendance_ratio * max_attendance
        
        EXCUSED не учитывается — занятие как будто не было.
        
        Args:
            transfer_attendance: Снапшот посещаемости из переводов
                {total_lessons, present, late, excused, absent}
        """
        max_score = settings.get_max_component_points(settings.attendance_weight)
        
        # Подсчёт из текущих записей
        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0
        
        for record in attendance_records:
            if record.status == AttendanceStatus.PRESENT:
                present_count += 1
            elif record.status == AttendanceStatus.LATE:
                late_count += 1
            elif record.status == AttendanceStatus.EXCUSED:
                excused_count += 1
            elif record.status == AttendanceStatus.ABSENT:
                absent_count += 1
        
        # Добавляем данные из снапшотов переводов
        if transfer_attendance:
            present_count += transfer_attendance.get("present", 0)
            late_count += transfer_attendance.get("late", 0)
            excused_count += transfer_attendance.get("excused", 0)
            absent_count += transfer_attendance.get("absent", 0)
        
        total_classes = present_count + late_count + excused_count + absent_count
        counted_classes = present_count + late_count + absent_count  # Без EXCUSED
        
        if counted_classes == 0:
            ratio = 0.0
        else:
            # present = 1.0, late = late_coef, absent = 0
            effective_attendance = present_count + (late_count * settings.late_coef)
            ratio = effective_attendance / counted_classes
        
        score = ratio * max_score
        
        return AttendanceScoreResult(
            score=round(score, 2),
            max_score=max_score,
            ratio=round(ratio, 4),
            total_classes=total_classes,
            counted_classes=counted_classes,
            present_count=present_count,
            late_count=late_count,
            excused_count=excused_count,
            absent_count=absent_count
        )
