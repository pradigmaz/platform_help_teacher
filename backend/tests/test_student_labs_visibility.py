from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.student.labs import get_my_labs
from app.models.lab import Lab
from app.models.user import User, UserRole
from app.services.deadline_semantics import calculate_visibility_state
from app.services.lab_visibility.models import LabVisibilityInfo
from app.services.lab_visibility.service import LabVisibilityService
from app.services.lab_visibility.visibility_calculator import (
    _calculate_single_lab_visibility,
    calculate_visibility_for_subject,
)


def _build_lab(number: int, subject_id, *, sequential: bool = True) -> Lab:
    return Lab(
        id=uuid4(),
        number=number,
        subject_id=subject_id,
        title=f"Lab {number}",
        max_grade=5,
        is_sequential=sequential,
        is_published=True,
        deleted_at=None,
    )


def _build_student(group_id) -> User:
    return User(
        id=uuid4(),
        full_name="Щедрина Анжелина Павловна",
        role=UserRole.STUDENT,
        group_id=group_id,
        subgroup=2,
        is_active=True,
    )


@pytest.fixture(autouse=True)
def patch_current_semester_offerings(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.list_group_subject_ids_for_current_semester",
        AsyncMock(return_value=()),
    )


def test_single_lab_visibility_exposes_traceable_lesson_index():
    visibility = _calculate_single_lab_visibility(
        lab_number=2,
        lab_dates={2: (date(2026, 3, 1), date(2026, 3, 15))},
        ordered_lessons=[
            (2, date(2026, 3, 1), 1),
            (3, date(2026, 3, 8), 1),
            (4, date(2026, 3, 15), 1),
        ],
        labs_deadlines={2: (1, 2)},
        labs_ids={},
        extensions_map={},
        excused_lab_numbers=set(),
        today=date(2026, 3, 15),
    )

    assert visibility.lesson_index == 2
    assert visibility.current_max_grade == 4


class TestStudentLabsVisibility:
    @pytest.mark.asyncio
    async def test_keeps_future_lab_in_list_as_locked(self, mock_db, monkeypatch):
        subject_id = uuid4()
        group_id = uuid4()
        student = _build_student(group_id)
        labs = [_build_lab(number, subject_id) for number in range(1, 5)]

        async def fake_visible_numbers(*args, **kwargs):
            return {subject_id: [1, 2, 3]}

        async def fake_batch_visibility(*args, **kwargs):
            return {
                1: LabVisibilityInfo(lab_number=1, is_visible=True),
                2: LabVisibilityInfo(lab_number=2, is_visible=True),
                3: LabVisibilityInfo(lab_number=3, is_visible=True),
                4: LabVisibilityInfo(
                    lab_number=4,
                    is_visible=False,
                    visible_from=date(2026, 3, 20),
                ),
            }

        async def fake_published_labs(db):
            return labs

        async def fake_submissions(db, user_id):
            return {}

        async def fake_journal_grades(db, user_id):
            return {
                subject_id: {
                    1: SimpleNamespace(grade=5),
                    2: SimpleNamespace(grade=5),
                    3: SimpleNamespace(grade=5),
                }
            }

        async def fake_position(db, current_user):
            return 1

        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visible_lab_numbers_by_subject",
            fake_visible_numbers,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_group_subject_ids",
            AsyncMock(return_value={subject_id}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_batch_visibility_info",
            fake_batch_visibility,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_published_labs",
            fake_published_labs,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_submissions",
            fake_submissions,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_journal_grades_by_subject",
            fake_journal_grades,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
            fake_position,
        )

        result = await get_my_labs(MagicMock(), db=mock_db, current_user=student)

        assert [lab["number"] for lab in result] == [1, 2, 3, 4]
        assert result[-1]["is_available"] is False
        assert result[-1]["visible_from"] == "2026-03-20"

    @pytest.mark.asyncio
    async def test_hides_labs_from_unrelated_subjects(self, mock_db, monkeypatch):
        visible_subject_id = uuid4()
        hidden_subject_id = uuid4()
        group_id = uuid4()
        student = _build_student(group_id)
        labs = [_build_lab(1, visible_subject_id), _build_lab(1, hidden_subject_id)]

        async def fake_visible_numbers(*args, **kwargs):
            return {visible_subject_id: [1]}

        async def fake_batch_visibility(*args, **kwargs):
            return {
                1: LabVisibilityInfo(lab_number=1, is_visible=True),
            }

        async def fake_published_labs(db):
            return labs

        async def fake_submissions(db, user_id):
            return {}

        async def fake_journal_grades(db, user_id):
            return {}

        async def fake_position(db, current_user):
            return 1

        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visible_lab_numbers_by_subject",
            fake_visible_numbers,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_group_subject_ids",
            AsyncMock(return_value={visible_subject_id}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_batch_visibility_info",
            fake_batch_visibility,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_published_labs",
            fake_published_labs,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_submissions",
            fake_submissions,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_journal_grades_by_subject",
            fake_journal_grades,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
            fake_position,
        )

        result = await get_my_labs(MagicMock(), db=mock_db, current_user=student)

        assert [(lab["number"], lab["title"]) for lab in result] == [(1, "Lab 1")]

    @pytest.mark.asyncio
    async def test_offerings_hide_historical_subjects_even_if_lessons_still_exist(self, mock_db, monkeypatch):
        visible_subject_id = uuid4()
        stale_subject_id = uuid4()
        group_id = uuid4()
        student = _build_student(group_id)
        labs = [_build_lab(1, visible_subject_id), _build_lab(1, stale_subject_id)]

        monkeypatch.setattr(
            "app.api.v1.endpoints.student.lab_queries.list_group_subject_ids_for_current_semester",
            AsyncMock(return_value=(visible_subject_id,)),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visible_lab_numbers_by_subject",
            AsyncMock(return_value={visible_subject_id: [1], stale_subject_id: [1]}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_batch_visibility_info",
            AsyncMock(return_value={1: LabVisibilityInfo(lab_number=1, is_visible=True)}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_published_labs",
            AsyncMock(return_value=labs),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_submissions",
            AsyncMock(return_value={}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_journal_grades_by_subject",
            AsyncMock(return_value={}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
            AsyncMock(return_value=1),
        )

        result = await get_my_labs(MagicMock(), db=mock_db, current_user=student)

        assert [lab["subject_id"] for lab in result] == [str(visible_subject_id)]

    @pytest.mark.asyncio
    async def test_keeps_visibility_for_subjects_with_same_lab_numbers(self, mock_db, monkeypatch):
        first_subject_id = uuid4()
        second_subject_id = uuid4()
        group_id = uuid4()
        student = _build_student(group_id)
        labs = [
            _build_lab(1, first_subject_id, sequential=False),
            _build_lab(2, first_subject_id, sequential=False),
            _build_lab(1, second_subject_id, sequential=False),
        ]

        async def fake_visible_numbers(*args, **kwargs):
            return {first_subject_id: [1, 2], second_subject_id: [1]}

        async def fake_batch_visibility(*args, **kwargs):
            subject_id = next(iter(kwargs["labs_subjects"].values()))
            return {
                lab_number: LabVisibilityInfo(
                    lab_number=lab_number,
                    is_visible=subject_id == first_subject_id or lab_number != 1,
                )
                for lab_number in kwargs["lab_numbers"]
            }

        async def fake_published_labs(db):
            return labs

        async def fake_submissions(db, user_id):
            return {}

        async def fake_journal_grades(db, user_id):
            return {}

        async def fake_position(db, current_user):
            return 1

        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visible_lab_numbers_by_subject",
            fake_visible_numbers,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_group_subject_ids",
            AsyncMock(return_value={first_subject_id, second_subject_id}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_batch_visibility_info",
            fake_batch_visibility,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_published_labs",
            fake_published_labs,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_submissions",
            fake_submissions,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_journal_grades_by_subject",
            fake_journal_grades,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
            fake_position,
        )

        result = await get_my_labs(MagicMock(), db=mock_db, current_user=student)

        assert [(lab["number"], lab["is_available"]) for lab in result] == [(1, True), (2, True), (1, False)]

    @pytest.mark.asyncio
    async def test_keeps_future_lab_for_group_subject_even_without_visible_slots(self, mock_db, monkeypatch):
        subject_id = uuid4()
        group_id = uuid4()
        student = _build_student(group_id)
        labs = [_build_lab(1, subject_id)]

        async def fake_visible_numbers(*args, **kwargs):
            return {}

        async def fake_batch_visibility(*args, **kwargs):
            return {
                1: LabVisibilityInfo(
                    lab_number=1,
                    is_visible=False,
                    visible_from=date(2026, 3, 29),
                )
            }

        async def fake_published_labs(db):
            return labs

        async def fake_submissions(db, user_id):
            return {}

        async def fake_journal_grades(db, user_id):
            return {}

        async def fake_position(db, current_user):
            return 1

        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visible_lab_numbers_by_subject",
            fake_visible_numbers,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_group_subject_ids",
            AsyncMock(return_value={subject_id}),
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.LabVisibilityService.get_batch_visibility_info",
            fake_batch_visibility,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_published_labs",
            fake_published_labs,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_submissions",
            fake_submissions,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_user_journal_grades_by_subject",
            fake_journal_grades,
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
            fake_position,
        )

        result = await get_my_labs(MagicMock(), db=mock_db, current_user=student)

        assert [lab["number"] for lab in result] == [1]
        assert result[0]["is_available"] is False
        assert result[0]["visible_from"] == "2026-03-29"


class TestDeadlineVisibilitySemantics:
    def test_deadline_allows_the_next_pair_when_limit_is_one(self):
        state = calculate_visibility_state(
            lessons_after=1,
            visible_from=date(2026, 3, 1),
            today=date(2026, 3, 8),
            deadline_5_lessons=1,
            deadline_4_lessons=None,
        )

        assert state.deadline_5_status == "active"
        assert state.lessons_until_deadline_5 == 0

    def test_repeated_lab_slots_consume_deadline_budget(self):
        info = _calculate_single_lab_visibility(
            lab_number=1,
            lab_dates={1: (date(2026, 3, 1), date(2026, 3, 15))},
            ordered_lessons=[
                (1, date(2026, 3, 1), 1),
                (1, date(2026, 3, 8), 1),
                (2, date(2026, 3, 15), 1),
            ],
            labs_deadlines={1: (1, None)},
            labs_ids={},
            extensions_map={},
            excused_lab_numbers=set(),
            today=date(2026, 3, 15),
        )

        assert info.deadline_5_status == "expired"
        assert info.current_max_grade == 4

    def test_excused_origin_disables_deadline_for_student_visibility(self):
        info = _calculate_single_lab_visibility(
            lab_number=1,
            lab_dates={1: (date(2026, 3, 1), date(2026, 3, 15))},
            ordered_lessons=[
                (1, date(2026, 3, 1), 1),
                (2, date(2026, 3, 8), 1),
                (3, date(2026, 3, 15), 1),
            ],
            labs_deadlines={1: (1, 2)},
            labs_ids={},
            extensions_map={},
            excused_lab_numbers={1},
            today=date(2026, 3, 15),
        )

        assert info.current_max_grade == 5
        assert info.deadline_5_status is None
        assert info.deadline_4_status is None
        assert info.is_excused_origin is True


@pytest.mark.asyncio
async def test_visibility_counts_unassigned_lab_practice_slots_same_as_teacher():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(
            all=lambda: [SimpleNamespace(work_number=1, min_date=date(2026, 3, 1), max_date=date(2026, 3, 1))]
        )
    )

    ordered_lessons_mock = AsyncMock(
        return_value=[
            (uuid4(), 1, date(2026, 3, 1), 1),
            (uuid4(), None, date(2026, 3, 8), 1),
        ]
    )

    from app.services.lab_visibility import visibility_calculator as visibility_module

    original_loader = visibility_module.load_ordered_deadline_lessons
    visibility_module.load_ordered_deadline_lessons = ordered_lessons_mock
    try:
        result = await calculate_visibility_for_subject(
            mock_db,
            lab_numbers=[1],
            group_id=uuid4(),
            subgroup=2,
            labs_deadlines={1: (0, None)},
            subject_id=uuid4(),
            today=date(2026, 3, 8),
        )
    finally:
        visibility_module.load_ordered_deadline_lessons = original_loader

    assert result[1].current_max_grade == 4
    assert result[1].lesson_index == 1


@pytest.mark.asyncio
async def test_get_visibility_info_passes_lab_id_for_extension_lookup(mock_db, monkeypatch):
    lab_id = uuid4()
    group_id = uuid4()
    subject_id = uuid4()
    captured_kwargs = {}

    async def fake_batch(self, **kwargs):
        captured_kwargs.update(kwargs)
        return {3: LabVisibilityInfo(lab_number=3, is_visible=True)}

    monkeypatch.setattr(LabVisibilityService, "get_batch_visibility_info", fake_batch)

    service = LabVisibilityService(mock_db)
    await service.get_visibility_info(
        lab_number=3,
        group_id=group_id,
        subgroup=2,
        deadline_5_lessons=2,
        deadline_4_lessons=4,
        subject_id=subject_id,
        lab_id=lab_id,
    )

    assert captured_kwargs["labs_ids"] == {3: lab_id}


@pytest.mark.asyncio
async def test_get_visibility_info_passes_student_id_for_excused_lookup(mock_db, monkeypatch):
    student_id = uuid4()
    captured_kwargs = {}

    async def fake_batch(self, **kwargs):
        captured_kwargs.update(kwargs)
        return {3: LabVisibilityInfo(lab_number=3, is_visible=True)}

    monkeypatch.setattr(LabVisibilityService, "get_batch_visibility_info", fake_batch)

    service = LabVisibilityService(mock_db)
    await service.get_visibility_info(
        lab_number=3,
        group_id=uuid4(),
        subgroup=2,
        deadline_5_lessons=2,
        deadline_4_lessons=4,
        subject_id=uuid4(),
        lab_id=uuid4(),
        student_id=student_id,
    )

    assert captured_kwargs["student_id"] == student_id


@pytest.mark.asyncio
async def test_student_labs_list_exposes_deadline_trace(mock_db, monkeypatch):
    subject_id = uuid4()
    group_id = uuid4()
    student = _build_student(group_id)
    labs = [_build_lab(3, subject_id, sequential=False)]

    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visible_lab_numbers_by_subject",
        AsyncMock(return_value={subject_id: [3]}),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.LabVisibilityService.get_group_subject_ids",
        AsyncMock(return_value={subject_id}),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.LabVisibilityService.get_batch_visibility_info",
        AsyncMock(
            return_value={
                3: LabVisibilityInfo(
                    lab_number=3,
                    is_visible=True,
                    current_max_grade=4,
                    lesson_index=2,
                    has_extension=True,
                    extension_bonus=1,
                )
            }
        ),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.get_published_labs",
        AsyncMock(return_value=labs),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.get_user_submissions",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.get_user_journal_grades_by_subject",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
        AsyncMock(return_value=1),
    )

    result = await get_my_labs(MagicMock(), db=mock_db, current_user=student)

    assert result[0]["deadline_trace"]["current_max_grade"] == 4
    assert result[0]["deadline_trace"]["lesson_index"] == 2
    assert result[0]["deadline_trace"]["effective_deadline_5_lessons"] is None
