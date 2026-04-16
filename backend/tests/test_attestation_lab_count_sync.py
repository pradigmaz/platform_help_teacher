from unittest.mock import AsyncMock, patch

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lab_settings import GradingScale as LabGradingScale
from app.models.lab_settings import LabSettings
from app.schemas.attestation import AttestationSettingsUpdate
from app.schemas.lab_settings import LabSettingsUpdate
from app.services.attestation.settings import AttestationSettingsManager
from app.services.lab_settings_service import LabSettingsService


def _make_attestation_settings(
    attestation_type: AttestationType,
    *,
    labs_count_first: int,
    labs_count_second: int,
) -> AttestationSettings:
    return AttestationSettings(
        attestation_type=attestation_type,
        labs_weight=70.0,
        attendance_weight=20.0,
        activity_reserve=10.0,
        labs_count_first=labs_count_first,
        labs_count_second=labs_count_second,
        grade_4_coef=0.7,
        grade_3_coef=0.4,
        late_coef=0.5,
        absent_coef=0.0,
        activity_enabled=True,
    )


def _make_lab_settings(labs_count: int) -> LabSettings:
    return LabSettings(
        labs_count=labs_count,
        grading_scale=LabGradingScale.TEN,
        default_max_grade=10,
    )


class AsyncMockResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_get_settings_syncs_stale_attestation_rows_from_first_and_second_sources(mock_db):
    first_settings = _make_attestation_settings(
        AttestationType.FIRST,
        labs_count_first=5,
        labs_count_second=3,
    )
    second_settings = _make_attestation_settings(
        AttestationType.SECOND,
        labs_count_first=9,
        labs_count_second=7,
    )
    manager = AttestationSettingsManager(mock_db)

    with (
        patch.object(
            manager,
            "_get_raw_settings",
            side_effect=[second_settings, first_settings, second_settings, second_settings],
        ),
        patch(
            "app.services.attestation.lab_count_sync.get_total_labs_count",
            AsyncMock(return_value=12),
        ),
        patch.object(manager, "_invalidate_caches", AsyncMock()),
    ):
        settings = await manager.get_settings(AttestationType.SECOND)

    assert settings is second_settings
    assert second_settings.labs_count_first == 5
    assert second_settings.labs_count_second == 7
    assert first_settings.labs_count_second == 7
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_first_settings_uses_shared_total_labs_contract(mock_db):
    first_settings = _make_attestation_settings(
        AttestationType.FIRST,
        labs_count_first=4,
        labs_count_second=6,
    )
    manager = AttestationSettingsManager(mock_db)
    settings_update = AttestationSettingsUpdate(
        attestation_type=AttestationType.FIRST,
        labs_count_first=7,
        labs_count_second=20,
        grade_4_coef=0.8,
    )

    async def fake_sync(*, first_required_override: int | None = None, second_required_override: int | None = None):
        assert first_required_override == 7
        assert second_required_override is None
        first_settings.labs_count_first = 7
        first_settings.labs_count_second = 6
        return {AttestationType.FIRST, AttestationType.SECOND}

    with (
        patch.object(manager, "get_or_create_settings", AsyncMock(return_value=first_settings)),
        patch.object(manager, "_sync_lab_counts", AsyncMock(side_effect=fake_sync)),
        patch.object(manager, "_invalidate_caches", AsyncMock()),
    ):
        settings = await manager.update_settings(settings_update)

    assert settings is first_settings
    assert first_settings.grade_4_coef == 0.8
    assert first_settings.labs_count_first == 7
    assert first_settings.labs_count_second == 6
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(first_settings)


@pytest.mark.asyncio
async def test_update_second_settings_respects_manual_second_count_edits(mock_db):
    second_settings = _make_attestation_settings(
        AttestationType.SECOND,
        labs_count_first=6,
        labs_count_second=4,
    )
    manager = AttestationSettingsManager(mock_db)
    settings_update = AttestationSettingsUpdate(
        attestation_type=AttestationType.SECOND,
        labs_count_first=1,
        labs_count_second=0,
        grade_4_coef=0.8,
    )

    async def fake_sync(*, first_required_override: int | None = None, second_required_override: int | None = None):
        assert first_required_override is None
        assert second_required_override == 0
        second_settings.labs_count_first = 6
        second_settings.labs_count_second = 0
        return {AttestationType.SECOND}

    with (
        patch.object(manager, "get_or_create_settings", AsyncMock(return_value=second_settings)),
        patch.object(manager, "_sync_lab_counts", AsyncMock(side_effect=fake_sync)),
        patch.object(manager, "_invalidate_caches", AsyncMock()),
    ):
        settings = await manager.update_settings(settings_update)

    assert settings is second_settings
    assert second_settings.grade_4_coef == 0.8
    assert second_settings.labs_count_first == 6
    assert second_settings.labs_count_second == 0
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(second_settings)


@pytest.mark.asyncio
async def test_lab_settings_update_keeps_existing_attestation_thresholds_when_total_is_valid(mock_db):
    service = LabSettingsService()
    lab_settings = _make_lab_settings(10)
    first_settings = _make_attestation_settings(
        AttestationType.FIRST,
        labs_count_first=6,
        labs_count_second=4,
    )
    second_settings = _make_attestation_settings(
        AttestationType.SECOND,
        labs_count_first=6,
        labs_count_second=4,
    )

    mock_db.execute.side_effect = [
        AsyncMockResult(lab_settings),
        AsyncMockResult(first_settings),
        AsyncMockResult(second_settings),
    ]

    settings = await service.update_lab_settings(mock_db, LabSettingsUpdate(labs_count=12))

    assert settings is lab_settings
    assert lab_settings.labs_count == 12
    assert first_settings.labs_count_first == 6
    assert first_settings.labs_count_second == 4
    assert second_settings.labs_count_first == 6
    assert second_settings.labs_count_second == 4
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(lab_settings)


@pytest.mark.asyncio
async def test_lab_settings_update_rejects_total_below_first_requirement(mock_db):
    service = LabSettingsService()
    lab_settings = _make_lab_settings(10)
    first_settings = _make_attestation_settings(
        AttestationType.FIRST,
        labs_count_first=8,
        labs_count_second=2,
    )
    second_settings = _make_attestation_settings(
        AttestationType.SECOND,
        labs_count_first=8,
        labs_count_second=2,
    )

    mock_db.execute.side_effect = [
        AsyncMockResult(lab_settings),
        AsyncMockResult(first_settings),
        AsyncMockResult(second_settings),
    ]

    with pytest.raises(ValueError, match="не может быть меньше суммарного количества"):
        await service.update_lab_settings(mock_db, LabSettingsUpdate(labs_count=9))

    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_attestation_lab_counts_uses_first_row_for_first_and_second_row_for_second(mock_db):
    first_settings = _make_attestation_settings(
        AttestationType.FIRST,
        labs_count_first=4,
        labs_count_second=3,
    )
    second_settings = _make_attestation_settings(
        AttestationType.SECOND,
        labs_count_first=9,
        labs_count_second=4,
    )

    with patch("app.services.attestation.lab_count_sync.get_total_labs_count", AsyncMock(return_value=10)):
        from app.services.attestation.lab_count_sync import sync_attestation_lab_counts

        changed_types = await sync_attestation_lab_counts(
            mock_db,
            first_settings=first_settings,
            second_settings=second_settings,
        )

    assert changed_types == {AttestationType.FIRST, AttestationType.SECOND}
    assert first_settings.labs_count_first == 4
    assert first_settings.labs_count_second == 4
    assert second_settings.labs_count_first == 4
    assert second_settings.labs_count_second == 4
