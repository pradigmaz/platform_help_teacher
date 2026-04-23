"""Resolve offering-scoped academic policy with legacy fallback."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_subject_offering import FinalControlType, GroupSubjectOffering
from app.models.group_subject_offering_policy import GroupSubjectOfferingPolicy
from app.models.lab_settings import LabSettings
from app.services.attestation.lab_count_sync import DEFAULT_TOTAL_LABS_COUNT
from app.services.attestation.subject_scope import build_period_semester_keys

from .offering_policy_validation import EffectiveOfferingPolicy, validate_offering_policy


def _exam_only_automatic(offering: GroupSubjectOffering | None, enabled: bool) -> bool:
    return bool(enabled and offering is not None and offering.final_control_type == FinalControlType.EXAM)


def _policy_from_row(
    row: GroupSubjectOfferingPolicy,
    offering: GroupSubjectOffering | None,
) -> EffectiveOfferingPolicy:
    return validate_offering_policy(
        EffectiveOfferingPolicy(
            offering_id=row.offering_id,
            source="explicit",
            total_labs=row.total_labs,
            labs_required_first=row.labs_required_first,
            labs_required_second_total=row.labs_required_second_total,
            exam_admission_required_labs=row.exam_admission_required_labs,
            automatic_enabled=_exam_only_automatic(offering, row.automatic_enabled),
            automatic_places=row.automatic_places,
            automatic_required_labs_total=row.automatic_required_labs_total,
        )
    )


async def _legacy_policy(db: AsyncSession, offering: GroupSubjectOffering | None) -> EffectiveOfferingPolicy:
    lab_result = await db.execute(select(LabSettings).limit(1))
    lab_settings = lab_result.scalar_one_or_none()
    total_labs = lab_settings.labs_count if lab_settings else DEFAULT_TOTAL_LABS_COUNT

    first_result = await db.execute(
        select(AttestationSettings).where(AttestationSettings.attestation_type == AttestationType.FIRST)
    )
    first_settings = first_result.scalar_one_or_none()
    second_result = await db.execute(
        select(AttestationSettings).where(AttestationSettings.attestation_type == AttestationType.SECOND)
    )
    second_settings = second_result.scalar_one_or_none()

    first_required = first_settings.labs_count_first if first_settings else min(8, total_labs)
    second_extra = second_settings.labs_count_second if second_settings else max(total_labs - first_required, 0)
    second_total = first_required + second_extra
    return validate_offering_policy(
        EffectiveOfferingPolicy(
            offering_id=offering.id if offering else None,
            source="legacy",
            total_labs=total_labs,
            labs_required_first=first_required,
            labs_required_second_total=second_total,
            exam_admission_required_labs=second_total,
            automatic_enabled=_exam_only_automatic(
                offering,
                lab_settings.automatic_enabled if lab_settings else True,
            ),
            automatic_places=lab_settings.automatic_places if lab_settings else None,
            automatic_required_labs_total=total_labs,
        )
    )


async def resolve_offering_policy(
    db: AsyncSession,
    offering: GroupSubjectOffering | None,
) -> EffectiveOfferingPolicy:
    """Return explicit policy for an offering, or derived legacy fallback."""
    if offering is None:
        return await _legacy_policy(db, None)

    result = await db.execute(
        select(GroupSubjectOfferingPolicy).where(GroupSubjectOfferingPolicy.offering_id == offering.id)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return _policy_from_row(row, offering)
    return await _legacy_policy(db, offering)


async def resolve_offering_policy_for_group_subject(
    db: AsyncSession,
    *,
    group_id: UUID,
    subject_id: UUID | None,
    settings: AttestationSettings,
) -> EffectiveOfferingPolicy:
    """Resolve policy through the current group/subject/semester scope."""
    if subject_id is None:
        return await _legacy_policy(db, None)

    period_start, period_end = settings.get_effective_period()
    result = await db.execute(
        select(GroupSubjectOffering)
        .where(GroupSubjectOffering.group_id == group_id)
        .where(GroupSubjectOffering.subject_id == subject_id)
        .where(GroupSubjectOffering.semester.in_(build_period_semester_keys(period_start, period_end)))
        .order_by(GroupSubjectOffering.semester.desc())
        .limit(1)
    )
    return await resolve_offering_policy(db, result.scalar_one_or_none())


async def upsert_offering_policy(
    db: AsyncSession,
    *,
    offering: GroupSubjectOffering,
    policy: EffectiveOfferingPolicy,
) -> GroupSubjectOfferingPolicy:
    """Create or update one offering policy row without touching legacy globals."""
    validate_offering_policy(policy)
    result = await db.execute(
        select(GroupSubjectOfferingPolicy).where(GroupSubjectOfferingPolicy.offering_id == offering.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = GroupSubjectOfferingPolicy(offering_id=offering.id)
        db.add(row)

    row.total_labs = policy.total_labs
    row.labs_required_first = policy.labs_required_first
    row.labs_required_second_total = policy.labs_required_second_total
    row.exam_admission_required_labs = policy.exam_admission_required_labs
    row.automatic_enabled = policy.automatic_enabled
    row.automatic_places = policy.automatic_places
    row.automatic_required_labs_total = policy.automatic_required_labs_total
    await db.flush()
    return row
