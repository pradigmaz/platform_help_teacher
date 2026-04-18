from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.automatic_pass_refusal import AutomaticPassRefusal
from app.models.group_subject_offering import GroupSubjectOffering
from app.models.user import User, UserRole
from app.services.schedule_constants import today_msk
from app.services.semester_utils import get_semester


def build_semester_key(academic_year: int, semester: int) -> str:
    return f"{academic_year}-{semester}"


async def get_current_semester_key(db: AsyncSession) -> str:
    result = await db.execute(
        select(AttestationSettings.semester_start_date).where(
            AttestationSettings.attestation_type == AttestationType.FIRST
        )
    )
    semester_start = result.scalar_one_or_none()
    if semester_start:
        if semester_start.month >= 9:
            return build_semester_key(semester_start.year, 1)
        return build_semester_key(semester_start.year - 1, 2)

    now = today_msk()
    if now.month >= 9:
        return build_semester_key(now.year, 1)
    return build_semester_key(now.year - 1, 2)


async def ensure_group_subject_offering(
    db: AsyncSession,
    *,
    group_id: UUID,
    subject_id: UUID,
    semester: str,
) -> GroupSubjectOffering:
    result = await db.execute(
        select(GroupSubjectOffering).where(
            GroupSubjectOffering.group_id == group_id,
            GroupSubjectOffering.subject_id == subject_id,
            GroupSubjectOffering.semester == semester,
        )
    )
    offering = result.scalar_one_or_none()
    if offering is not None:
        return offering

    offering = GroupSubjectOffering(group_id=group_id, subject_id=subject_id, semester=semester)
    db.add(offering)
    await db.flush()
    return offering


async def get_group_subject_offering(
    db: AsyncSession,
    *,
    group_id: UUID,
    subject_id: UUID,
    semester: str,
) -> GroupSubjectOffering | None:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(selectinload(GroupSubjectOffering.group), selectinload(GroupSubjectOffering.subject))
        .where(
            GroupSubjectOffering.group_id == group_id,
            GroupSubjectOffering.subject_id == subject_id,
            GroupSubjectOffering.semester == semester,
        )
    )
    return result.scalar_one_or_none()


async def get_group_subject_offering_for_date(
    db: AsyncSession,
    *,
    group_id: UUID,
    subject_id: UUID,
    lesson_date: date,
) -> GroupSubjectOffering | None:
    return await get_group_subject_offering(
        db,
        group_id=group_id,
        subject_id=subject_id,
        semester=get_semester(lesson_date),
    )


async def ensure_group_subject_offering_for_date(
    db: AsyncSession,
    *,
    group_id: UUID,
    subject_id: UUID,
    lesson_date: date,
) -> GroupSubjectOffering:
    return await ensure_group_subject_offering(
        db,
        group_id=group_id,
        subject_id=subject_id,
        semester=get_semester(lesson_date),
    )


async def list_group_subject_offerings(
    db: AsyncSession,
    *,
    semester: str,
) -> list[GroupSubjectOffering]:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(selectinload(GroupSubjectOffering.group), selectinload(GroupSubjectOffering.subject))
        .where(GroupSubjectOffering.semester == semester)
        .order_by(GroupSubjectOffering.semester.asc(), GroupSubjectOffering.group_id.asc(), GroupSubjectOffering.subject_id.asc())
    )
    return list(result.scalars().all())


async def list_group_subject_offerings_for_group(
    db: AsyncSession,
    *,
    group_id: UUID,
    semester: str,
) -> list[GroupSubjectOffering]:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(selectinload(GroupSubjectOffering.subject))
        .where(
            GroupSubjectOffering.group_id == group_id,
            GroupSubjectOffering.semester == semester,
        )
        .order_by(GroupSubjectOffering.subject_id.asc())
    )
    return list(result.scalars().all())


async def list_group_subject_ids_for_current_semester(
    db: AsyncSession,
    *,
    group_id: UUID,
) -> tuple[UUID, ...]:
    semester = await get_current_semester_key(db)
    offerings = await list_group_subject_offerings_for_group(db, group_id=group_id, semester=semester)
    return tuple(offering.subject_id for offering in offerings if offering.subject_id is not None)


async def list_offering_refusals(
    db: AsyncSession,
    *,
    offering_id: UUID,
) -> list[AutomaticPassRefusal]:
    result = await db.execute(
        select(AutomaticPassRefusal)
        .options(selectinload(AutomaticPassRefusal.student), selectinload(AutomaticPassRefusal.declined_by_admin))
        .where(AutomaticPassRefusal.offering_id == offering_id)
        .order_by(AutomaticPassRefusal.created_at.asc())
    )
    return list(result.scalars().all())


async def upsert_automatic_pass_refusal(
    db: AsyncSession,
    *,
    offering_id: UUID,
    student_id: UUID,
    declined_by_admin_id: UUID | None,
    reason: str | None,
) -> AutomaticPassRefusal:
    result = await db.execute(
        select(AutomaticPassRefusal).where(
            AutomaticPassRefusal.offering_id == offering_id,
            AutomaticPassRefusal.student_id == student_id,
        )
    )
    refusal = result.scalar_one_or_none()
    if refusal is None:
        refusal = AutomaticPassRefusal(
            offering_id=offering_id,
            student_id=student_id,
            declined_by_admin_id=declined_by_admin_id,
            reason=reason,
        )
        db.add(refusal)
        await db.flush()
        return refusal

    refusal.declined_by_admin_id = declined_by_admin_id
    refusal.reason = reason
    await db.flush()
    return refusal


async def clear_automatic_pass_refusal(
    db: AsyncSession,
    *,
    offering_id: UUID,
    student_id: UUID,
) -> bool:
    result = await db.execute(
        select(AutomaticPassRefusal).where(
            AutomaticPassRefusal.offering_id == offering_id,
            AutomaticPassRefusal.student_id == student_id,
        )
    )
    refusal = result.scalar_one_or_none()
    if refusal is None:
        return False

    await db.delete(refusal)
    await db.flush()
    return True


async def list_active_students_for_group(db: AsyncSession, *, group_id: UUID) -> list[User]:
    result = await db.execute(
        select(User)
        .where(
            User.group_id == group_id,
            User.role == UserRole.STUDENT,
            User.is_active.is_(True),
        )
        .order_by(User.full_name.asc(), User.id.asc())
    )
    return list(result.scalars().all())
