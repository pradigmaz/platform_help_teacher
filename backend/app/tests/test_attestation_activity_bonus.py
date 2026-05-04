"""Tests for treating attestation activity as a capped bonus."""

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.schemas.attestation import AttestationSettingsUpdate
from app.services.attestation.settings import AttestationSettingsManager


def make_settings_update(
    *,
    labs_weight: float = 70.0,
    attendance_weight: float = 30.0,
    activity_reserve: float = 10.0,
) -> AttestationSettingsUpdate:
    return AttestationSettingsUpdate(
        attestation_type=AttestationType.FIRST,
        labs_weight=labs_weight,
        attendance_weight=attendance_weight,
        activity_reserve=activity_reserve,
        labs_count_first=4,
        labs_count_second=6,
        grade_4_coef=0.7,
        grade_3_coef=0.4,
        late_coef=0.5,
        absent_coef=0.0,
        self_works_enabled=False,
        self_works_weight=0.0,
        self_works_count=2,
        colloquium_enabled=False,
        colloquium_weight=0.0,
        colloquium_count=1,
        activity_enabled=True,
        expected_lessons_per_week=2,
        semester_start_date=None,
    )


def test_settings_schema_accepts_bonus_activity_outside_base_weight_sum():
    settings = make_settings_update(labs_weight=70.0, attendance_weight=30.0, activity_reserve=10.0)

    assert settings.labs_weight + settings.attendance_weight == 100.0
    assert settings.activity_reserve == 10.0


def test_settings_schema_rejects_base_weights_below_100_even_when_activity_fills_gap():
    with pytest.raises(ValidationError, match="Базовые веса"):
        make_settings_update(labs_weight=70.0, attendance_weight=20.0, activity_reserve=10.0)


def test_model_weight_validation_excludes_activity_reserve_from_base_sum():
    settings = AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=30.0,
        activity_reserve=10.0,
    )

    assert settings.validate_weights() is True


def test_model_weight_validation_rejects_old_reserved_activity_shape():
    settings = AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=20.0,
        activity_reserve=10.0,
    )

    assert settings.validate_weights() is False


def test_score_preview_describes_activity_as_bonus_cap():
    settings = AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=30.0,
        activity_reserve=10.0,
        labs_count_first=4,
        expected_lessons_per_week=2,
    )

    preview = AttestationSettingsManager.build_score_preview(settings)

    activity_row = next(row for row in preview if "Активность" in row.component)
    assert activity_row.max_points == 3.5
    assert "бонус" in activity_row.unit_label.lower()


def test_settings_update_schema_allows_omitting_legacy_lab_thresholds():
    settings = AttestationSettingsUpdate(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=30.0,
        activity_reserve=10.0,
        grade_4_coef=0.7,
        grade_3_coef=0.4,
        late_coef=0.5,
        absent_coef=0.0,
        self_works_enabled=False,
        self_works_weight=0.0,
        self_works_count=2,
        colloquium_enabled=False,
        colloquium_weight=0.0,
        colloquium_count=1,
        activity_enabled=True,
        expected_lessons_per_week=2,
        semester_start_date=None,
    )

    assert settings.labs_count_first is None
    assert settings.labs_count_second is None


@pytest.mark.asyncio
async def test_update_settings_preserves_legacy_lab_thresholds_when_omitted():
    existing = AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=30.0,
        activity_reserve=10.0,
        labs_count_first=4,
        labs_count_second=6,
        grade_4_coef=0.7,
        grade_3_coef=0.4,
        late_coef=0.5,
        absent_coef=0.0,
        self_works_enabled=False,
        self_works_weight=0.0,
        self_works_count=2,
        colloquium_enabled=False,
        colloquium_weight=0.0,
        colloquium_count=1,
        activity_enabled=True,
        expected_lessons_per_week=2,
    )
    db = AsyncMock()
    manager = AttestationSettingsManager(db)
    manager.get_or_create_settings = AsyncMock(return_value=existing)
    manager._sync_lab_counts = AsyncMock(return_value=set())
    manager._invalidate_caches = AsyncMock()

    settings = AttestationSettingsUpdate(
        attestation_type=AttestationType.FIRST,
        labs_weight=60.0,
        attendance_weight=40.0,
        activity_reserve=10.0,
        grade_4_coef=0.7,
        grade_3_coef=0.4,
        late_coef=0.5,
        absent_coef=0.0,
        self_works_enabled=False,
        self_works_weight=0.0,
        self_works_count=2,
        colloquium_enabled=False,
        colloquium_weight=0.0,
        colloquium_count=1,
        activity_enabled=True,
        expected_lessons_per_week=2,
        semester_start_date=None,
    )

    await manager.update_settings(settings)

    assert existing.labs_count_first == 4
    assert existing.labs_count_second == 6
    manager._sync_lab_counts.assert_awaited_once_with(
        first_required_override=None,
        second_required_override=None,
    )
