"""
Построение данных студентов для отчётов.
"""
from typing import Any, Dict, List, Tuple

from app.models.group_report import GroupReport
from app.models.user import User
from app.schemas.report import PublicStudentData


def build_student_data(
    student: User, 
    result: Any, 
    att_stats: Dict,
    lab_stats: Dict, 
    notes: List[str], 
    report: GroupReport
) -> PublicStudentData:
    """Построить данные студента."""
    is_passing = result.is_passing if result else False
    
    return PublicStudentData(
        id=student.id,
        name=student.full_name if report.show_names else None,
        subgroup=student.subgroup,
        total_score=result.total_score if result and report.show_grades else None,
        lab_score=result.breakdown.labs_score if result and report.show_grades else None,
        attendance_score=result.breakdown.attendance_score if result and report.show_grades else None,
        activity_score=result.breakdown.activity_score if result and report.show_grades else None,
        grade=result.grade if result and report.show_grades else None,
        is_passing=is_passing if report.show_grades else None,
        attendance_rate=att_stats.get('rate') if report.show_attendance else None,
        present_count=att_stats.get('present') if report.show_attendance else None,
        absent_count=att_stats.get('absent') if report.show_attendance else None,
        late_count=att_stats.get('late') if report.show_attendance else None,
        excused_count=att_stats.get('excused') if report.show_attendance else None,
        labs_completed=lab_stats.get('completed') if report.show_grades else None,
        labs_total=lab_stats.get('total') if report.show_grades else None,
        needs_attention=not is_passing,
        notes=notes if report.show_notes and notes else None,
    )


def process_students(
    students: List[User],
    results_map: Dict,
    attendance_data: Dict,
    labs_data: Dict,
    notes_map: Dict,
    report: GroupReport
) -> Tuple[List[PublicStudentData], int, int, float]:
    """Обработка данных студентов.
    
    Returns:
        Tuple[students_data, passing_count, failing_count, total_score_sum]
    """
    students_data = []
    passing_count = 0
    failing_count = 0
    total_score_sum = 0.0
    
    for student in students:
        result = results_map.get(student.id)
        att_stats = attendance_data.get(student.id, {})
        lab_stats = labs_data.get(student.id, {})
        
        is_passing = result.is_passing if result else False
        if is_passing:
            passing_count += 1
        else:
            failing_count += 1
        
        if result:
            total_score_sum += result.total_score
        
        student_data = build_student_data(
            student, result, att_stats, lab_stats,
            notes_map.get(student.id, []), report
        )
        students_data.append(student_data)
    
    return students_data, passing_count, failing_count, total_score_sum
