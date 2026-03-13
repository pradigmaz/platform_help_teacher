from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.student.labs import get_my_labs
from app.models.lab import Lab
from app.models.user import User, UserRole
from app.services.lab_visibility.models import LabVisibilityInfo


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
                (subject_id, 1): LabVisibilityInfo(lab_number=1, is_visible=True),
                (subject_id, 2): LabVisibilityInfo(lab_number=2, is_visible=True),
                (subject_id, 3): LabVisibilityInfo(lab_number=3, is_visible=True),
                (subject_id, 4): LabVisibilityInfo(
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
                (visible_subject_id, 1): LabVisibilityInfo(lab_number=1, is_visible=True),
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
