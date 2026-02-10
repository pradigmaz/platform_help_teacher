"""
Построение отчётов группы.
"""

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group import Group
from app.models.group_report import GroupReport, ReportType
from app.models.user import User
from app.schemas.report import PublicReportData

from .base_helpers import get_filtered_teacher_contacts


def build_empty_report(
    report: GroupReport,
    group: Group | None,
    teacher: User | None,
    attestation_type: str = "first",
    max_points: int = 35,
    min_passing_points: int = 20,
    is_second_available: bool = False,
) -> PublicReportData:
    """Построить пустой отчёт."""
    att_type = AttestationType.SECOND if attestation_type == "second" else AttestationType.FIRST
    grade_scale = AttestationSettings.get_grade_scale(att_type)
    grade_scale_json = {k: list(v) for k, v in grade_scale.items()}

    return PublicReportData(
        group_code=group.code if group else "",
        group_name=group.name if group else None,
        subject_name=None,
        report_type=ReportType(report.report_type),
        teacher_contacts=get_filtered_teacher_contacts(teacher, "report") if teacher else None,
        show_names=report.show_names,
        show_grades=report.show_grades,
        show_attendance=report.show_attendance,
        show_notes=report.show_notes,
        show_rating=report.show_rating,
        total_students=0,
        passing_students=0 if report.show_grades else None,
        failing_students=0 if report.show_grades else None,
        average_score=None,
        max_points=max_points,
        min_passing_points=min_passing_points,
        grade_scale=grade_scale_json if report.show_grades else None,
        attestation_type=attestation_type,
        is_second_available=is_second_available,
        has_subgroups=False,
        students=[],
        attendance_distribution=None,
        attendance_stats=None,
        lab_progress=None,
        grade_distribution=None,
    )
