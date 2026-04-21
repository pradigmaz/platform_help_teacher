from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.deps import get_current_active_superuser, get_current_teacher, get_current_user
from app.api.deps import get_db as deps_get_db
from app.api.v1.endpoints.admin_exam_banks import router as admin_exam_banks_router
from app.api.v1.endpoints.admin_subject_offerings import router as admin_router
from app.api.v1.endpoints.student.exam_prep import router as student_router
from app.db.session import get_db as session_get_db
from app.models.group_subject_offering import FinalControlType
from app.models.user import User, UserRole
from tests.support.http import router_client


def make_student_user(group_id) -> User:
    return User(
        id=uuid4(),
        full_name="Студент Тестов",
        username="student_test",
        role=UserRole.STUDENT,
        group_id=group_id,
        is_active=True,
    )


def make_admin_user() -> User:
    return User(
        id=uuid4(),
        full_name="Администратор Тестов",
        username="admin_test",
        role=UserRole.ADMIN,
        is_active=True,
    )


def make_offering(*, final_control_type: FinalControlType, questions: list[dict] | None = None):
    exam_question_bank = None
    if questions:
        exam_question_bank = SimpleNamespace(
            id=uuid4(),
            subject_id=uuid4(),
            semester="2099-1",
            questions=questions,
            subject=SimpleNamespace(name="Компьютерные сети"),
            offerings=[],
        )
    return SimpleNamespace(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=uuid4(),
        semester="2099-1",
        final_control_type=final_control_type,
        exam_question_bank_id=exam_question_bank.id if exam_question_bank else None,
        exam_question_bank=exam_question_bank,
        exam_prep_questions=questions or [],
        subject=SimpleNamespace(name="Компьютерные сети"),
        group=SimpleNamespace(name="ИС-101"),
    )


def make_bank(*, offerings: list[SimpleNamespace] | None = None, questions: list[dict] | None = None):
    subject_id = offerings[0].subject_id if offerings else uuid4()
    bank = SimpleNamespace(
        id=uuid4(),
        subject_id=subject_id,
        semester="2099-1",
        questions=questions or [],
        subject=SimpleNamespace(name="Компьютерные сети"),
        offerings=offerings or [],
    )
    for offering in offerings or []:
        offering.exam_question_bank_id = bank.id
        offering.exam_question_bank = bank
    return bank


@pytest.mark.asyncio
async def test_student_exam_prep_offerings_list_filters_non_exam_items():
    db = AsyncMock()
    student = make_student_user(uuid4())
    exam_offering = make_offering(
        final_control_type=FinalControlType.EXAM,
        questions=[{"id": "q1", "prompt": {"text": "Что такое DNS?"}}],
    )
    credit_offering = make_offering(final_control_type=FinalControlType.CREDIT)

    async def override_student() -> User:
        return student

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.student.exam_prep.get_current_semester_key",
        new=AsyncMock(return_value="2099-1"),
    ), patch(
        "app.api.v1.endpoints.student.exam_prep.list_group_subject_offerings_for_group",
        new=AsyncMock(return_value=[credit_offering, exam_offering]),
    ):
        async with router_client(
            (student_router, "/student"),
            dependency_overrides={
                get_current_user: override_student,
                deps_get_db: override_db,
            },
        ) as client:
            response = await client.get("/student/exam-prep/offerings")

    assert response.status_code == 200
    assert response.json() == [
        {
            "offering_id": str(exam_offering.id),
            "subject_id": str(exam_offering.subject_id),
            "subject_name": "Компьютерные сети",
            "semester": "2099-1",
            "questions_count": 1,
        }
    ]


@pytest.mark.asyncio
async def test_student_exam_prep_detail_returns_payload_and_404():
    db = AsyncMock()
    student = make_student_user(uuid4())
    offering = make_offering(
        final_control_type=FinalControlType.EXAM,
        questions=[
            {
                "id": "q1",
                "prompt": {"text": "Что такое стек TCP/IP?"},
                "answer": {"text": "Базовая сетевая модель"},
            }
        ],
    )

    async def override_student() -> User:
        return student

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.student.exam_prep._get_student_exam_offering_or_404",
        new=AsyncMock(return_value=offering),
    ):
        async with router_client(
            (student_router, "/student"),
            dependency_overrides={
                get_current_user: override_student,
                deps_get_db: override_db,
            },
        ) as client:
            response = await client.get(f"/student/exam-prep/{offering.id}")

    assert response.status_code == 200
    assert response.json()["questions"][0]["answer"]["text"] == "Базовая сетевая модель"

    with patch(
        "app.api.v1.endpoints.student.exam_prep._get_student_exam_offering_or_404",
        new=AsyncMock(side_effect=HTTPException(status_code=404, detail="Экзамен не найден")),
    ):
        async with router_client(
            (student_router, "/student"),
            dependency_overrides={
                get_current_user: override_student,
                deps_get_db: override_db,
            },
        ) as client:
            missing_response = await client.get(f"/student/exam-prep/{uuid4()}")

    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_admin_subject_offerings_count_questions_from_assigned_bank():
    admin = make_admin_user()
    db = SimpleNamespace(commit=AsyncMock())
    offering = make_offering(final_control_type=FinalControlType.EXAM)
    bank = make_bank(
        offerings=[offering],
        questions=[{"id": "exam-q1", "prompt": {"text": "Что такое маршрутизация?"}}],
    )
    offering.subject_id = bank.subject_id
    offering.subject = bank.subject

    async def override_admin() -> User:
        return admin

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.admin_subject_offerings.list_group_subject_offerings",
        new=AsyncMock(return_value=[offering]),
    ):
        async with router_client(
            (admin_router, "/admin/subjects"),
            dependency_overrides={
                get_current_teacher: override_admin,
                get_current_active_superuser: override_admin,
                session_get_db: override_db,
            },
        ) as client:
            offerings_response = await client.get("/admin/subjects/offerings", params={"semester": "2099-1"})

    assert offerings_response.status_code == 200
    payload = offerings_response.json()[0]
    assert payload["exam_prep_questions_count"] == 1
    assert payload["exam_question_bank_id"] == str(bank.id)


@pytest.mark.asyncio
async def test_admin_exam_bank_groups_and_context_return_shared_state():
    admin = make_admin_user()
    db = AsyncMock()
    offering_a = make_offering(final_control_type=FinalControlType.EXAM)
    offering_b = make_offering(final_control_type=FinalControlType.EXAM)
    offering_b.group = SimpleNamespace(name="ИС-102")
    bank = make_bank(
        offerings=[offering_a],
        questions=[{"id": "q1", "prompt": {"text": "Что такое DNS?"}}],
    )
    offering_a.subject_id = bank.subject_id
    offering_b.subject_id = bank.subject_id
    offering_a.subject = bank.subject
    offering_b.subject = bank.subject

    async def override_admin() -> User:
        return admin

    async def override_db():
        return db

    execute_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [bank]))

    with patch(
        "app.api.v1.endpoints.admin_exam_banks.list_group_subject_offerings",
        new=AsyncMock(return_value=[offering_a, offering_b]),
    ), patch(
        "app.api.v1.endpoints.admin_exam_banks.get_current_semester_key",
        new=AsyncMock(return_value="2099-1"),
    ), patch.object(db, "execute", AsyncMock(return_value=execute_result)), patch(
        "app.api.v1.endpoints.admin_exam_banks.get_exam_offering_or_404",
        new=AsyncMock(return_value=offering_b),
    ):
        async with router_client(
            (admin_exam_banks_router, "/admin/exams"),
            dependency_overrides={
                get_current_teacher: override_admin,
                session_get_db: override_db,
            },
        ) as client:
            groups_response = await client.get("/admin/exams/groups")
            context_response = await client.get(f"/admin/exams/offerings/{offering_b.id}/context")

    assert groups_response.status_code == 200
    groups_payload = groups_response.json()
    assert groups_payload[0]["banks"][0]["questions_count"] == 1
    assert groups_payload[0]["unassigned_offerings"][0]["group_name"] == "ИС-102"

    assert context_response.status_code == 200
    context_payload = context_response.json()
    assert context_payload["bank"] is None
    assert context_payload["compatible_banks"][0]["bank_id"] == str(bank.id)


@pytest.mark.asyncio
async def test_assign_and_split_exam_bank_update_offering_links():
    admin = make_admin_user()
    added_items: list[SimpleNamespace] = []

    def add_item(item):
        added_items.append(item)

    db = SimpleNamespace(commit=AsyncMock(), add=add_item, flush=AsyncMock())
    offering_a = make_offering(final_control_type=FinalControlType.EXAM)
    offering_b = make_offering(final_control_type=FinalControlType.EXAM)
    offering_b.group = SimpleNamespace(name="ИС-102")
    bank = make_bank(
        offerings=[offering_a],
        questions=[{"id": "q1", "prompt": {"text": "Что такое DNS?"}}],
    )
    offering_a.subject_id = bank.subject_id
    offering_b.subject_id = bank.subject_id
    offering_a.subject = bank.subject
    offering_b.subject = bank.subject

    async def override_admin() -> User:
        return admin

    async def override_db():
        return db

    async def get_bank(*_args, **_kwargs):
        return bank

    async def get_offering(*_args):
        if _args[-1] == offering_a.id:
            return offering_a
        return offering_b

    with patch("app.api.v1.endpoints.admin_exam_banks.get_exam_question_bank_or_404", new=get_bank), patch(
        "app.api.v1.endpoints.admin_exam_banks.get_exam_offering_or_404",
        new=get_offering,
    ):
        async with router_client(
            (admin_exam_banks_router, "/admin/exams"),
            dependency_overrides={
                get_current_active_superuser: override_admin,
                get_current_teacher: override_admin,
                session_get_db: override_db,
            },
        ) as client:
            assign_response = await client.post(
                f"/admin/exams/banks/{bank.id}/assign",
                json={"offering_ids": [str(offering_b.id)]},
            )
            # Mirror ORM state after assign: the relationship and FK point to the same shared bank.
            offering_b.exam_question_bank_id = bank.id
            bank.offerings = [offering_a, offering_b]
            split_response = await client.post(
                f"/admin/exams/banks/{bank.id}/split",
                json={"offering_ids": [str(offering_b.id)]},
            )

    assert assign_response.status_code == 200
    assert assign_response.json()["bank_id"] == str(bank.id)
    assert split_response.status_code == 200
    assert offering_b.exam_question_bank is not bank
    assert offering_b.exam_question_bank in added_items
