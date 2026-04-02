"""Preservation tests for attestation period calculation contracts."""

from datetime import date, timedelta

from app.models.attestation_settings import (
    AttestationSettings,
    AttestationType,
    FIRST_ATTESTATION_WEEK,
)


class TestFirstPeriodPreservation:
    """FIRST attestation period should stay stable."""

    def test_first_period_with_semester_start(self):
        semester_start = date(2025, 9, 1)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
        )

        period_start, period_end = settings.get_effective_period()

        assert period_start == semester_start
        assert period_end == semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK)

    def test_first_period_duration_is_8_weeks(self):
        semester_start = date(2025, 2, 3)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
        )

        period_start, period_end = settings.get_effective_period()

        assert (period_end - period_start).days / 7 == FIRST_ATTESTATION_WEEK


class TestExplicitDatesPreservation:
    """Explicit period dates should override derived defaults."""

    def test_explicit_dates_returned_as_is_first(self):
        start = date(2025, 9, 15)
        end = date(2025, 11, 10)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            period_start_date=start,
            period_end_date=end,
        )

        assert settings.get_effective_period() == (start, end)

    def test_explicit_dates_returned_as_is_second(self):
        start = date(2025, 10, 27)
        end = date(2025, 12, 22)
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            period_start_date=start,
            period_end_date=end,
        )

        assert settings.get_effective_period() == (start, end)

    def test_explicit_dates_override_semester_start(self):
        start = date(2025, 9, 15)
        end = date(2025, 11, 10)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
            period_start_date=start,
            period_end_date=end,
        )

        assert settings.get_effective_period() == (start, end)


class TestCalculateAttestationPeriodPreservation:
    """Static helper should keep its baseline semantics."""

    def test_first_attestation_period_static(self):
        semester_start = date(2025, 9, 1)
        start, end = AttestationSettings.calculate_attestation_period(
            semester_start,
            AttestationType.FIRST,
        )

        assert start == semester_start
        assert end == semester_start + timedelta(weeks=8)

    def test_period_start_before_end(self):
        for att_type in [AttestationType.FIRST, AttestationType.SECOND]:
            start, end = AttestationSettings.calculate_attestation_period(
                date(2025, 9, 1),
                att_type,
            )
            assert start < end
