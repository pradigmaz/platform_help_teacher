"""Traceable deadline context objects shared by visibility and attestation paths."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DeadlineContext:
    lab_number: int
    origin_lesson_id: UUID | None
    lesson_index: int | None
    extension_bonus: int
    is_excused_origin: bool


def build_deadline_context_for_visibility(
    *,
    lab_number: int,
    ordered_lessons: list[tuple[int | None, object, int]],
    lab_id: UUID | None,
    extensions_map: dict[UUID, int],
    excused_lab_numbers: set[int],
) -> DeadlineContext:
    origin_index = next(
        (idx for idx, (work_number, _, _) in enumerate(ordered_lessons) if work_number == lab_number), None
    )
    lesson_index = len(ordered_lessons) - origin_index - 1 if origin_index is not None else 0
    extension_bonus = extensions_map.get(lab_id, 0) if lab_id else 0
    return DeadlineContext(
        lab_number=lab_number,
        origin_lesson_id=None,
        lesson_index=lesson_index,
        extension_bonus=extension_bonus,
        is_excused_origin=lab_number in excused_lab_numbers,
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
    lesson_index = None if current_pos is None or origin_pos is None else current_pos - origin_pos
    return DeadlineContext(
        lab_number=lab_number,
        origin_lesson_id=origin_lesson_id,
        lesson_index=lesson_index,
        extension_bonus=extension_bonus,
        is_excused_origin=is_excused_origin,
    )
