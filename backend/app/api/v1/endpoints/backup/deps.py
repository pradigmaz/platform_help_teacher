"""
Backup API dependencies.
"""

from app.services.backup.backup_service import BackupService
from app.services.backup.restore_service import RestoreService


def get_backup_service() -> BackupService:
    """Dependency for backup service."""
    return BackupService()


def get_restore_service() -> RestoreService:
    """Dependency for restore service."""
    return RestoreService()
