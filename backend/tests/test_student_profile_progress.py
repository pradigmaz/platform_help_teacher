from datetime import UTC, datetime
from uuid import uuid4

from app.models import Lab, Submission
from app.models.submission import SubmissionStatus
from app.services.lab_progress_read_model import normalize_lab_progress
from app.services.student_service import StudentService


def _build_lab(lab_number: int, subject_id):
    return Lab(
        id=uuid4(),
        number=lab_number,
        title=f"Lab {lab_number}",
        subject_id=subject_id,
        max_grade=5,
        is_published=True,
    )


def test_normalize_lab_progress_prefers_journal_acceptance_over_rejected_submission():
    submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=uuid4(),
        status=SubmissionStatus.REJECTED,
        is_manual=True,
        grade=2,
        feedback="legacy reject",
    )
    journal_grade = type("Grade", (), {"grade": 4})()

    progress = normalize_lab_progress(submission, journal_grade)

    assert progress.normalized_status == SubmissionStatus.ACCEPTED.value
    assert progress.grade == 4
    assert progress.acceptance_source == "journal"


def test_normalize_lab_progress_maps_legacy_review_status_to_pending():
    submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=uuid4(),
        status=SubmissionStatus.IN_REVIEW,
        is_manual=True,
        grade=5,
        ready_at=datetime.now(UTC),
    )

    progress = normalize_lab_progress(submission, None)

    assert progress.normalized_status == SubmissionStatus.READY.value
    assert progress.grade is None


def test_student_service_calculate_stats_uses_normalized_progress():
    service = StudentService(db=None)
    subject_id = uuid4()
    accepted_lab = _build_lab(1, subject_id)
    pending_lab = _build_lab(2, subject_id)
    rejected_lab = _build_lab(3, subject_id)

    accepted_submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=accepted_lab.id,
        status=SubmissionStatus.REJECTED,
        is_manual=True,
        feedback="old reject",
    )
    pending_submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=pending_lab.id,
        status=SubmissionStatus.IN_REVIEW,
        is_manual=True,
        ready_at=datetime.now(UTC),
    )
    rejected_submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=rejected_lab.id,
        status=SubmissionStatus.REQ_CHANGES,
        is_manual=True,
        feedback="fix it",
    )

    journal_grades = {
        (subject_id, 1): type("Grade", (), {"grade": 5})(),
    }

    labs_data, stats = service._calculate_stats(
        labs=[accepted_lab, pending_lab, rejected_lab],
        subs_map={
            accepted_lab.id: accepted_submission,
            pending_lab.id: pending_submission,
            rejected_lab.id: rejected_submission,
        },
        grades_map=journal_grades,
        include_details=True,
    )

    assert stats.labs_accepted == 1
    assert stats.labs_pending == 1
    assert stats.labs_rejected == 1
    assert stats.points_earned == 5
    assert {lab.lab_id: lab.normalized_status for lab in labs_data} == {
        accepted_lab.id: SubmissionStatus.ACCEPTED.value,
        pending_lab.id: SubmissionStatus.READY.value,
        rejected_lab.id: SubmissionStatus.REJECTED.value,
    }


def test_student_service_calculate_stats_skips_lab_payload_for_shell_mode():
    service = StudentService(db=None)
    subject_id = uuid4()
    accepted_lab = _build_lab(1, subject_id)

    accepted_submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=accepted_lab.id,
        status=SubmissionStatus.ACCEPTED,
        is_manual=True,
        grade=5,
    )

    labs_data, stats = service._calculate_stats(
        labs=[accepted_lab],
        subs_map={accepted_lab.id: accepted_submission},
        grades_map={},
        include_details=False,
    )

    assert labs_data == []
    assert stats.labs_total == 1
    assert stats.labs_accepted == 1
    assert stats.points_earned == 5
    assert stats.points_max == 5


def test_student_service_apply_group_ranking_calculates_place_and_percentile():
    service = StudentService(db=None)
    student_id = uuid4()
    higher_student_id = uuid4()
    lower_student_id = uuid4()
    stats = service._calculate_stats([], {}, {}, include_details=False)[1]

    service._apply_group_ranking(
        stats,
        [
            (higher_student_id, 10),
            (student_id, 7),
            (lower_student_id, 3),
        ],
        student_id,
    )

    assert stats.group_total == 3
    assert stats.group_rank == 2
    assert stats.group_percentile == 50.0
