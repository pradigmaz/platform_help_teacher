"""Traceable deadline context objects shared by visibility and attestation paths."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DeadlineContext:
    lab_number: int
    origin_lesson_id: UUID | None
    lesson_index: int | None
    extension_bonus: int
    is_excused_origin: bool
    deadline_active: bool


def resolve_last_work_number_index(work_numbers: Sequence[int | None], lab_number: int) -> int | None:
    for idx in range(len(work_numbers) - 1, -1, -1):
        if work_numbers[idx] == lab_number:
            return idx
    return None


def build_deadline_context_for_visibility(
    *,
    lab_number: int,
    ordered_lessons: Sequence[tuple[UUID, int | None, object, int]],
    past_lesson_ids: set[UUID],
    lab_id: UUID | None,
    extensions_map: dict[UUID, int],
    excused_lab_numbers: set[int],
) -> DeadlineContext:
    activation_index = resolve_last_work_number_index(
        [work_number for _, work_number, _, _ in ordered_lessons],
        lab_number,
    )
    deadline_active = False
    lesson_index = 0
    if activation_index is not None:
        activation_lesson_id = ordered_lessons[activation_index][0]
        deadline_active = activation_lesson_id in past_lesson_ids
        if deadline_active:
            lesson_index = sum(
                1
                for idx, (lesson_id, _, _, _) in enumerate(ordered_lessons)
                if idx > activation_index and lesson_id in past_lesson_ids
            )
    extension_bonus = extensions_map.get(lab_id, 0) if lab_id else 0
    return DeadlineContext(
        lab_number=lab_number,
        origin_lesson_id=None,
        lesson_index=lesson_index,
        extension_bonus=extension_bonus,
        is_excused_origin=lab_number in excused_lab_numbers,
        deadline_active=deadline_active,
    )


def build_deadline_context_for_current_lesson(
    *,
    lab_number: int,
    origin_lesson_id: UUID | None,
    current_lesson_id: UUID,
    lesson_positions: dict[UUID, int],
    extension_bonus: int = 0,
    is_excused_origin: bool = False,
) -> DeadlineContext:
    current_pos = lesson_positions.get(current_lesson_id)
    origin_pos = lesson_positions.get(origin_lesson_id) if origin_lesson_id else None
    deadline_active = current_pos is not None and origin_pos is not None and current_pos >= origin_pos
    lesson_index = None if current_pos is None or origin_pos is None else max(current_pos - origin_pos, 0)
    return DeadlineContext(
        lab_number=lab_number,
        origin_lesson_id=origin_lesson_id,
        lesson_index=lesson_index,
        extension_bonus=extension_bonus,
        is_excused_origin=is_excused_origin,
        deadline_active=deadline_active,
    )
