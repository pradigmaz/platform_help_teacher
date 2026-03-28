from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_activities,
    admin_announcements,
    admin_attendance,
    admin_attestation,
    admin_audit,
    admin_audit_export,
    admin_impersonate,
    admin_journal,
    admin_lab_queue,
    admin_lab_schedule,
    admin_labs,
    admin_lectures,
    admin_notes,
    admin_rate_limit,
    admin_reports,
    admin_schedule,
    admin_schedule_parser,
    admin_schedule_sheet,
    admin_schedule_view,
    admin_security,
    admin_stats,
    admin_subjects,
    admin_work_submissions,
    admin_works,
    auth,
    feedback,
    feedback_attachments,
    groups,
    honeypot,
    labs,
    lectures,
    public_reports,
    public_semester,
    student,
    user_devices,
    user_sessions,
    users,
    webhooks,
)
from app.api.v1.endpoints.backup import router as backup_router

api_router = APIRouter()

# === HONEYPOT TRAPS (первыми, чтобы перехватывать до реальных роутов) ===
# Популярные пути для сканеров
api_router.include_router(honeypot.router, prefix="/phpMyAdmin", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/phpmyadmin", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/pma", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/mysql", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/wp-admin", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/administrator", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/debug", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/actuator", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/graphql", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/console", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/shell", tags=["honeypot"], include_in_schema=False)
# Фейковые админские эндпоинты (ловушки)
api_router.include_router(honeypot.router, prefix="/admin/config", tags=["honeypot"], include_in_schema=False)
api_router.include_router(
    honeypot.router,
    prefix="/admin/database",
    tags=["honeypot"],
    include_in_schema=False,
)
api_router.include_router(honeypot.router, prefix="/admin/dump", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/admin/sql", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/admin/shell", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/admin/console", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/admin/debug", tags=["honeypot"], include_in_schema=False)
api_router.include_router(honeypot.router, prefix="/admin/export", tags=["honeypot"], include_in_schema=False)
api_router.include_router(
    honeypot.router,
    prefix="/admin/backup/download",
    tags=["honeypot"],
    include_in_schema=False,
)

# === REAL ENDPOINTS ===

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(user_sessions.router, prefix="/users", tags=["user_sessions"])
api_router.include_router(user_devices.router, prefix="/users", tags=["user_devices"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Student endpoints
api_router.include_router(student.router, prefix="/student", tags=["student"])

# Подключил админку (разделенную)
api_router.include_router(admin_lab_queue.router, prefix="/admin/labs", tags=["admin_lab_queue"])
api_router.include_router(admin_labs.router, prefix="/admin", tags=["admin_labs"])
api_router.include_router(admin_attestation.router, prefix="/admin", tags=["admin_attestation"])
api_router.include_router(admin_attendance.router, prefix="/admin", tags=["admin_attendance"])
api_router.include_router(admin_stats.router, prefix="/admin", tags=["admin_stats"])
api_router.include_router(admin_activities.router, prefix="/admin", tags=["admin_activities"])
api_router.include_router(admin_works.router, prefix="/admin", tags=["admin_works"])
api_router.include_router(admin_work_submissions.router, prefix="/admin", tags=["admin_work_submissions"])
api_router.include_router(admin_schedule.router, prefix="/admin", tags=["admin_schedule"])
api_router.include_router(admin_schedule_sheet.router, prefix="/admin", tags=["admin_schedule"])
api_router.include_router(admin_schedule_view.router, prefix="/admin", tags=["admin_schedule"])
api_router.include_router(admin_journal.router, prefix="/admin/journal", tags=["admin_journal"])
api_router.include_router(admin_subjects.router, prefix="/admin/subjects", tags=["admin_subjects"])
api_router.include_router(
    admin_schedule_parser.router,
    prefix="/admin/schedule",
    tags=["admin_schedule_parser"],
)
api_router.include_router(admin_notes.router, prefix="/admin/notes", tags=["admin_notes"])
api_router.include_router(admin_lectures.router, prefix="/admin/lectures", tags=["admin_lectures"])
api_router.include_router(admin_reports.router, prefix="/admin", tags=["admin_reports"])
api_router.include_router(admin_audit_export.router, prefix="/admin/audit", tags=["admin_audit_export"])
api_router.include_router(admin_audit.router, prefix="/admin/audit", tags=["admin_audit"])
api_router.include_router(backup_router, prefix="/admin/backups", tags=["admin_backup"])
api_router.include_router(admin_rate_limit.router, prefix="/admin/rate-limits", tags=["admin_rate_limit"])
api_router.include_router(admin_security.router, prefix="/admin", tags=["admin_security"])
api_router.include_router(admin_impersonate.router, prefix="/admin", tags=["admin_impersonate"])
api_router.include_router(admin_lab_schedule.router, prefix="/admin/labs", tags=["admin_lab_schedule"])
api_router.include_router(
    admin_announcements.router,
    prefix="/admin/announcements",
    tags=["admin_announcements"],
)

api_router.include_router(feedback_attachments.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(labs.router, prefix="/labs", tags=["labs"])
api_router.include_router(lectures.router, prefix="/lectures", tags=["lectures"])

# Public endpoints (без авторизации)
api_router.include_router(public_reports.router, prefix="/public", tags=["public_reports"])
api_router.include_router(public_semester.router, prefix="/public", tags=["public_semester"])
