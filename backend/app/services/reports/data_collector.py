"""Facade for public report data collection."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport
from app.schemas.report import PublicReportData, StudentDetailData

from .group_report_collector import collect_group_report_data
from .student_detail_collector import _get_group_comparison_stats as collect_group_comparison_stats
from .student_detail_collector import collect_student_report_data


class ReportDataCollector:
    """Thin facade that delegates group and student report collection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_group_report_data(
        self,
        report: GroupReport,
        attestation_type: str = "first",
        subject_id: UUID | None = None,
    ) -> PublicReportData:
        """Collect public group report data."""
        return await collect_group_report_data(
            db=self.db,
            report=report,
            attestation_type=attestation_type,
            subject_id=subject_id,
        )

    async def get_student_report_data(
        self,
        report: GroupReport,
        student_id: UUID,
        attestation_type: str = "first",
        subject_id: UUID | None = None,
    ) -> StudentDetailData | None:
        """Collect detailed student report data."""
        return await collect_student_report_data(
            db=self.db,
            report=report,
            student_id=student_id,
            attestation_type=attestation_type,
            subject_id=subject_id,
        )

    async def _get_group_comparison_stats(
        self,
        group_id: UUID,
        student_id: UUID,
        student_score: float,
        attestation_type,
    ):
        return await collect_group_comparison_stats(
            self.db,
            group_id,
            student_id,
            student_score,
            attestation_type,
        )
