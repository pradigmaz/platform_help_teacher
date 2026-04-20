from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.deps import get_current_active_superuser, get_current_teacher, get_current_user
from app.api.deps import get_db as deps_get_db
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
    return SimpleNamespace(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=uuid4(),
        semester="2099-1",
        final_control_type=final_control_type,
        exam_prep_questions=questions or [],
        subject=SimpleNamespace(name="Компьютерные сети"),
        group=SimpleNamespace(name="ИС-101"),
    )


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
async def test_admin_exam_prep_roundtrip_updates_questions_count():
    admin = make_admin_user()
    db = SimpleNamespace(commit=AsyncMock())
    offering = make_offering(final_control_type=FinalControlType.EXAM)

    async def override_admin() -> User:
        return admin

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.admin_subject_offerings._get_offering_or_404",
        new=AsyncMock(return_value=offering),
    ), patch(
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
            empty_response = await client.get(f"/admin/subjects/offerings/{offering.id}/exam-prep")
            save_response = await client.put(
                f"/admin/subjects/offerings/{offering.id}/exam-prep",
                json={
                    "questions": [
                        {
                            "id": "exam-q1",
                            "prompt": {"text": "Что такое маршрутизация?"},
                            "answer": {"text": "Выбор пути передачи пакета"},
                        }
                    ]
                },
            )
            offerings_response = await client.get("/admin/subjects/offerings", params={"semester": "2099-1"})

    assert empty_response.status_code == 200
    assert empty_response.json()["questions_count"] == 0

    assert save_response.status_code == 200
    assert save_response.json()["questions_count"] == 1
    assert save_response.json()["questions"][0]["answer"]["text"] == "Выбор пути передачи пакета"
    assert db.commit.await_count == 1

    assert offerings_response.status_code == 200
    assert offerings_response.json()[0]["exam_prep_questions_count"] == 1
