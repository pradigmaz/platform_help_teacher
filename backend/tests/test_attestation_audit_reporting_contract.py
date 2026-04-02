"""Contract checks for attestation-aware report aggregation helpers."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationType


class TestGroupComparisonAttestationTypeContract:
    @pytest.mark.asyncio
    async def test_group_comparison_should_use_passed_attestation_type(self):
        from app.services.attestation.service import AttestationService
        from app.services.reports.student_detail_collector import _get_group_comparison_stats

        group_id = uuid4()
        student_id = uuid4()
        mock_db = AsyncMock()

        mock_student = MagicMock()
        mock_student.id = student_id
        mock_student.group_id = group_id

        mock_att_result = MagicMock()
        mock_att_result.total_score = 50.0
        mock_att_result.student_id = student_id

        with (
            patch("app.services.reports.student_detail_collector.get_group_students", return_value=[mock_student]),
            patch.object(
                AttestationService,
                "calculate_group_scores_batch",
                return_value=([mock_att_result], []),
            ) as mock_batch,
        ):
            await _get_group_comparison_stats(mock_db, group_id, student_id, 50.0, AttestationType.SECOND)

        assert mock_batch.called, "calculate_group_scores_batch не был вызван"
        call_kwargs = mock_batch.call_args
        used_type = call_kwargs.kwargs.get("attestation_type") or call_kwargs.args[1]
        assert used_type == AttestationType.SECOND, (
            f"Counterexample: used attestation_type={used_type}, expected SECOND"
        )
