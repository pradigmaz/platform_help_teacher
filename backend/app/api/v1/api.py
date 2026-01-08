from fastapi import APIRouter
from app.api.v1.endpoints import users, auth, webhooks, groups, labs, admin_labs, admin_attestation, admin_attendance, admin_stats, admin_activities, admin_works, admin_work_submissions, admin_schedule, admin_journal, student, admin_subjects, admin_schedule_parser, admin_notes, admin_lectures, lectures, admin_reports, public_reports, admin_lab_queue, admin_audit, admin_audit_export, admin_backup

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
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
api_router.include_router(admin_journal.router, prefix="/admin/journal", tags=["admin_journal"])
api_router.include_router(admin_subjects.router, prefix="/admin/subjects", tags=["admin_subjects"])
api_router.include_router(admin_schedule_parser.router, prefix="/admin/schedule", tags=["admin_schedule_parser"])
api_router.include_router(admin_notes.router, prefix="/admin/notes", tags=["admin_notes"])
api_router.include_router(admin_lectures.router, prefix="/admin/lectures", tags=["admin_lectures"])
api_router.include_router(admin_reports.router, prefix="/admin", tags=["admin_reports"])
api_router.include_router(admin_audit.router, prefix="/admin/audit", tags=["admin_audit"])
api_router.include_router(admin_audit_export.router, prefix="/admin/audit", tags=["admin_audit_export"])
api_router.include_router(admin_backup.router, prefix="/admin/backups", tags=["admin_backup"])

api_router.include_router(labs.router, prefix="/labs", tags=["labs"])
api_router.include_router(lectures.router, prefix="/lectures", tags=["lectures"])

# Public endpoints (без авторизации)
api_router.include_router(public_reports.router, prefix="/public", tags=["public_reports"])
