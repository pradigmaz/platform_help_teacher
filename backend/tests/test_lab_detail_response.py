from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.lab import LabDetailResponse


def test_lab_detail_response_hides_legacy_lesson_attachment():
    lab = SimpleNamespace(
        id=uuid4(),
        number=3,
        title="Lab 3",
        topic=None,
        goal=None,
        formatting_guide=None,
        description=None,
        theory_content=None,
        practice_content=None,
        variants=None,
        questions=None,
        deadline_5_lessons=2,
        deadline_4_lessons=4,
        max_grade=5,
        is_sequential=True,
        is_published=True,
        public_code="ABC123",
        subject_id=uuid4(),
        lesson_id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    response = LabDetailResponse.model_validate(lab)
    payload = response.model_dump(mode="json")

    assert "lesson_id" not in payload
