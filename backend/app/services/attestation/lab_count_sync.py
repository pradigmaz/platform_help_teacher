"""Helpers for synchronizing attestation lab counts with global lab settings."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lab_settings import LabSettings

DEFAULT_TOTAL_LABS_COUNT = 10


def resolve_total_labs_count(configured_total: int | None) -> int:
    """Return the configured total labs count or the backend default."""
    if configured_total is None:
        return DEFAULT_TOTAL_LABS_COUNT
    return configured_total


def validate_lab_counts(first_required: int, second_required: int, total_labs: int) -> tuple[int, int]:
    """Validate manual lab thresholds against the total labs count."""
    if total_labs < first_required + second_required:
        raise ValueError(
            "Общее количество лабораторных "
            f"({total_labs}) не может быть меньше суммарного количества "
            "лабораторных для аттестаций "
            f"({first_required + second_required})"
        )
    return first_required, second_required


def apply_synced_lab_counts(
    settings: AttestationSettings,
    first_required: int,
    second_required: int,
    total_labs: int,
) -> bool:
    """Apply synchronized lab counts to an attestation settings row."""
    synced_first, synced_second = validate_lab_counts(first_required, second_required, total_labs)
    changed = False

    if settings.labs_count_first != synced_first:
        settings.labs_count_first = synced_first
        changed = True
    if settings.labs_count_second != synced_second:
        settings.labs_count_second = synced_second
        changed = True

    return changed


async def get_total_labs_count(db: AsyncSession) -> int:
    """Load the configured total labs count."""
    result = await db.execute(select(LabSettings).limit(1))
    settings = result.scalar_one_or_none()
    configured_total = settings.labs_count if settings else None
    return resolve_total_labs_count(configured_total)


async def get_attestation_settings_row(
    db: AsyncSession,
    attestation_type: AttestationType,
) -> AttestationSettings | None:
    """Load a single attestation settings row without creating defaults."""
    result = await db.execute(
        select(AttestationSettings).where(AttestationSettings.attestation_type == attestation_type)
    )
    return result.scalar_one_or_none()


async def sync_attestation_lab_counts(
    db: AsyncSession,
    *,
    total_labs: int | None = None,
    first_required: int | None = None,
    second_required: int | None = None,
    first_settings: AttestationSettings | None = None,
    second_settings: AttestationSettings | None = None,
) -> set[AttestationType]:
    """Synchronize existing attestation settings rows to the same shared lab contract."""
    if first_settings is None:
        first_settings = await get_attestation_settings_row(db, AttestationType.FIRST)
    if second_settings is None:
        second_settings = await get_attestation_settings_row(db, AttestationType.SECOND)

    rows = [settings for settings in (first_settings, second_settings) if settings is not None]
    if not rows:
        return set()

    effective_total_labs = resolve_total_labs_count(total_labs)
    if total_labs is None:
        effective_total_labs = await get_total_labs_count(db)

    effective_first_required = first_required
    if effective_first_required is None:
        source_row = first_settings or rows[0]
        effective_first_required = source_row.labs_count_first

    effective_second_required = second_required
    if effective_second_required is None:
        source_row = second_settings or rows[0]
        effective_second_required = source_row.labs_count_second

    changed_types: set[AttestationType] = set()
    for settings in rows:
        if apply_synced_lab_counts(
            settings,
            effective_first_required,
            effective_second_required,
            effective_total_labs,
        ):
            changed_types.add(settings.attestation_type)

    return changed_types
