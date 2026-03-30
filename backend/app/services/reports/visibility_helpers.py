from typing import Any

from app.models.group_report import GroupReport


def apply_visibility_filter(data: dict[str, Any], report: GroupReport) -> dict[str, Any]:
    """Применение фильтра видимости к данным отчёта."""
    filtered = data.copy()

    if not report.show_names:
        filtered.pop("name", None)
        filtered.pop("full_name", None)

    if not report.show_grades:
        for key in ["total_score", "lab_score", "attendance_score", "activity_score", "grade", "is_passing"]:
            filtered.pop(key, None)

    if not report.show_attendance:
        for key in [
            "attendance_rate",
            "present_count",
            "absent_count",
            "late_count",
            "excused_count",
            "attendance_history",
        ]:
            filtered.pop(key, None)

    if not report.show_notes:
        filtered.pop("notes", None)

    if not report.show_rating:
        filtered.pop("rank_in_group", None)
        filtered.pop("group_average_score", None)

    return filtered
