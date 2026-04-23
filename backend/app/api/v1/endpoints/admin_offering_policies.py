"""Admin endpoints for offering-scoped academic policy."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.db.session import get_db
from app.models.group_subject_offering import GroupSubjectOffering
from app.models.user import User
from app.schemas.offering_policy import OfferingPolicyPayload, OfferingPolicyResponse
from app.services.offering_policy_resolver import resolve_offering_policy, upsert_offering_policy
from app.services.offering_policy_validation import EffectiveOfferingPolicy

router = APIRouter()


async def _get_offering_or_404(db: AsyncSession, offering_id: UUID) -> GroupSubjectOffering:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(selectinload(GroupSubjectOffering.group), selectinload(GroupSubjectOffering.subject))
        .where(GroupSubjectOffering.id == offering_id)
    )
    offering = result.scalar_one_or_none()
    if offering is None:
        raise HTTPException(status_code=404, detail="Связка предмета группы не найдена")
    return offering


def _to_response(policy: EffectiveOfferingPolicy) -> OfferingPolicyResponse:
    if policy.offering_id is None:
        raise HTTPException(status_code=404, detail="Policy is available only for a concrete offering")
    return OfferingPolicyResponse(
        offering_id=policy.offering_id,
        source=policy.source,
        total_labs=policy.total_labs,
        labs_required_first=policy.labs_required_first,
        labs_required_second_total=policy.labs_required_second_total,
        exam_admission_required_labs=policy.exam_admission_required_labs,
        automatic_enabled=policy.automatic_enabled,
        automatic_places=policy.automatic_places,
        automatic_required_labs_total=policy.automatic_required_labs_total,
        second_extra_required=policy.labs_required_second_extra,
        automatic_extra_required=policy.automatic_extra_required,
    )


@router.get("/offerings/{offering_id}/policy", response_model=OfferingPolicyResponse)
async def get_offering_policy(
    offering_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> OfferingPolicyResponse:
    offering = await _get_offering_or_404(db, offering_id)
    return _to_response(await resolve_offering_policy(db, offering))


@router.put("/offerings/{offering_id}/policy", response_model=OfferingPolicyResponse)
async def update_offering_policy(
    offering_id: UUID,
    payload: OfferingPolicyPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> OfferingPolicyResponse:
    offering = await _get_offering_or_404(db, offering_id)
    policy = EffectiveOfferingPolicy(
        offering_id=offering.id,
        source="explicit",
        total_labs=payload.total_labs,
        labs_required_first=payload.labs_required_first,
        labs_required_second_total=payload.labs_required_second_total,
        exam_admission_required_labs=payload.exam_admission_required_labs,
        automatic_enabled=payload.automatic_enabled,
        automatic_places=payload.automatic_places,
        automatic_required_labs_total=payload.automatic_required_labs_total,
    )
    await upsert_offering_policy(db, offering=offering, policy=policy)
    await db.commit()
    return _to_response(await resolve_offering_policy(db, offering))
