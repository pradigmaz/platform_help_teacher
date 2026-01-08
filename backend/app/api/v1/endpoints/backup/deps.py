"""
Backup API dependencies.
"""
from app.services.backup import BackupService, RestoreService


def get_backup_service() -> BackupService:
    """Dependency for backup service."""
    return BackupService()


def get_restore_service() -> RestoreService:
    """Dependency for restore service."""
    return RestoreService()
