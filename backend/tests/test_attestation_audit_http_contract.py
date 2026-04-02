"""HTTP-level contract checks for student attestation error handling."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.student.attestation import router
from app.services.attestation_service import AttestationService
from tests.support.http import router_client


class TestStudentAttestationHttpContract:
    @pytest.mark.asyncio
    async def test_system_error_should_return_http_500(self):
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.group_id = uuid4()
        mock_db = AsyncMock()

        async def override_user():
            return mock_user

        async def override_db():
            yield mock_db

        with patch.object(
            AttestationService,
            "calculate_student_score",
            side_effect=RuntimeError("Database connection failed"),
        ):
            async with router_client(
                router,
                dependency_overrides={get_current_user: override_user, get_db: override_db},
            ) as client:
                response = await client.get("/attestation/first")

        assert response.status_code == 500, (
            f"Counterexample: endpoint returned HTTP {response.status_code} with body {response.json()}"
        )

    @pytest.mark.asyncio
    async def test_system_error_should_not_return_total_score_zero(self):
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.group_id = uuid4()
        mock_db = AsyncMock()

        async def override_user():
            return mock_user

        async def override_db():
            yield mock_db

        with patch.object(
            AttestationService,
            "calculate_student_score",
            side_effect=RuntimeError("DB error"),
        ):
            async with router_client(
                router,
                dependency_overrides={get_current_user: override_user, get_db: override_db},
            ) as client:
                response = await client.get("/attestation/first")

        assert response.status_code == 500, (
            f"Counterexample: HTTP {response.status_code} with body {response.json()} for RuntimeError"
        )
