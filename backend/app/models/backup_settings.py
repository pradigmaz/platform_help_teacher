"""
Backup settings model.
Stores backup configuration in database.
"""
from sqlalchemy import Text, Integer, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class BackupSettings(Base, TimestampMixin):
    """Global backup settings (singleton row)."""
    __tablename__ = "backup_settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    
    # Schedule
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule_hour: Mapped[int] = mapped_column(Integer, default=3)  # 3:00 AM
    schedule_minute: Mapped[int] = mapped_column(Integer, default=0)
    
    # Retention
    retention_days: Mapped[int] = mapped_column(Integer, default=30)
    max_backups: Mapped[int] = mapped_column(Integer, default=10)
    
    # Storage
    storage_bucket: Mapped[str] = mapped_column(String(100), default="edu-backups")
    
    # Notifications (optional)
    notify_on_success: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=True)
