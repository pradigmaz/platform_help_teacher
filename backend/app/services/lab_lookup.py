"""Shared active-lab lookup helpers for legacy deadline/submission paths."""

import logging
from collections import defaultdict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab

logger = logging.getLogger(__name__)


def _rank_lab_candidate(lab: Lab) -> tuple[int, str, str]:
    created_at = getattr(lab, "created_at", None)
    created_at_str = created_at.isoformat() if created_at else ""
    return (1 if lab.is_published else 0, created_at_str, str(lab.id))


def _pick_preferred_lab(candidates: list[Lab], *, subject_id: UUID, published_only: bool) -> Lab | None:
    filtered = [lab for lab in candidates if lab.is_published] if published_only else list(candidates)
    if not filtered:
        return None

    if len(filtered) > 1:
        logger.warning(
            "Multiple active labs found for subject=%s number=%s; using preferred candidate",
            subject_id,
            filtered[0].number,
        )

    return max(filtered, key=_rank_lab_candidate)


def _extract_lab_rows(result) -> list[Lab]:
    scalar_one_or_none = getattr(result, "scalar_one_or_none", None)
    if callable(scalar_one_or_none):
        single = scalar_one_or_none()
        if isinstance(single, Lab):
            return [single]

    scalars = getattr(result, "scalars", None)
    if callable(scalars):
        scalar_result = scalars()
        all_rows = getattr(scalar_result, "all", None)
        if callable(all_rows):
            rows = all_rows()
            if isinstance(rows, (list, tuple)):
                return list(rows)
    return []


async def find_active_lab_by_subject_and_number(
    db: AsyncSession,
    subject_id: UUID,
    number: int,
    *,
    published_only: bool = False,
) -> Lab | None:
    labs = await find_active_labs_by_subject_and_numbers(
        db,
        subject_id,
        {number},
        published_only=published_only,
    )
    return labs.get(number)


async def find_active_labs_by_subject_and_numbers(
    db: AsyncSession,
    subject_id: UUID | None,
    numbers: set[int],
    *,
    published_only: bool = False,
) -> dict[int, Lab]:
    if subject_id is None or not numbers:
        return {}

    result = await db.execute(
        select(Lab)
        .where(
            and_(
                Lab.subject_id == subject_id,
                Lab.number.in_(numbers),
                Lab.deleted_at.is_(None),
            )
        )
        .order_by(Lab.number.asc(), Lab.is_published.desc(), Lab.created_at.desc(), Lab.id.desc())
    )

    candidates_by_number: dict[int, list[Lab]] = defaultdict(list)
    for lab in _extract_lab_rows(result):
        candidates_by_number[lab.number].append(lab)

    resolved: dict[int, Lab] = {}
    for number, candidates in candidates_by_number.items():
        preferred = _pick_preferred_lab(candidates, subject_id=subject_id, published_only=published_only)
        if preferred is not None:
            resolved[number] = preferred
    return resolved
