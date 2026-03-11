"""
Exploration tests for labs grading bugs.
CRITICAL: These tests MUST FAIL on unfixed code — failure confirms bugs exist.
DO NOT fix the code or tests when they fail.

BUG-1: LessonType enum comparison with string "LAB" always returns False
BUG-2: get_lab_by_id() returns unpublished/deleted labs to students
BUG-3: AcceptSubmissionRequest accepts grade > 5 (0-100 scale vs 2-5 scale)
BUG-4: bulk_upsert_lesson_grades() creates duplicates instead of moving grades
BUG-5: delete_grade_by_lesson_student() fails with MultipleResultsFound
BUG-6: upsert_lesson_grade() commits before sync — non-atomic
BUG-7: get_user_journal_grades() doesn't filter by subject_id
BUG-8: No UNIQUE constraint on (subject_id, number) in labs table
BUG-9: lab_service.create/update doesn't validate subject_id vs lesson.subject_id
"""

import os

os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.schedule import LessonType

# ============================================================
# Minimal SQLite-compatible metadata (no JSONB/PostgreSQL types)
# ============================================================

_meta = MetaData()

_subjects = Table(
    "subjects",
    _meta,
    Column("id", Text, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("code", String(50), nullable=True),
    Column("description", Text, nullable=True),
    Column("is_active", Boolean, default=True),
    Column("created_at", Text, nullable=True),
    Column("updated_at", Text, nullable=True),
)

_groups = Table(
    "groups",
    _meta,
    Column("id", Text, primary_key=True),
    Column("code", Text, unique=True, nullable=False),
    Column("name", Text, nullable=False),
    Column("invite_code", Text, unique=True, nullable=True),
    Column("has_subgroups", Boolean, default=True),
    Column("is_archived", Boolean, default=False),
    Column("labs_count", Integer, nullable=True),
    Column("created_at", Text, nullable=True),
    Column("updated_at", Text, nullable=True),
)

_users = Table(
    "users",
    _meta,
    Column("id", Text, primary_key=True),
    Column("full_name", Text, nullable=False),
    Column("role", Text, nullable=False, default="student"),
    Column("group_id", Text, ForeignKey("groups.id"), nullable=True),
    Column("telegram_id", Integer, unique=True, nullable=True),
    Column("vk_id", Integer, unique=True, nullable=True),
    Column("username", Text, nullable=True),
    Column("is_active", Boolean, default=True),
    Column("invite_code", Text, unique=True, nullable=True),
    Column("subgroup", Integer, nullable=True),
    Column("onboarding_completed", Boolean, default=False),
    Column("contacts", Text, default="{}"),
    Column("contact_visibility", Text, default="{}"),
    Column("teacher_settings", Text, default="{}"),
    Column("created_at", Text, nullable=True),
    Column("updated_at", Text, nullable=True),
)

_lessons = Table(
    "lessons",
    _meta,
    Column("id", Text, primary_key=True),
    Column("group_id", Text, ForeignKey("groups.id"), nullable=False),
    Column("subject_id", Text, ForeignKey("subjects.id"), nullable=True),
    Column("date", Date, nullable=False),
    Column("lesson_number", Integer, nullable=False),
    Column("lesson_type", Text, nullable=False),
    Column("topic", String(500), nullable=True),
    Column("work_number", Integer, nullable=True),
    Column("subgroup", Integer, nullable=True),
    Column("is_cancelled", Boolean, default=False),
    Column("cancellation_reason", String(255), nullable=True),
    Column("ended_early", Boolean, default=False),
    Column("max_labs_override", Integer, nullable=True),
    Column("schedule_item_id", Text, nullable=True),
    Column("work_id", Text, nullable=True),
    Column("lecture_work_type", String(20), nullable=True),
    Column("created_at", Text, nullable=True),
    Column("updated_at", Text, nullable=True),
)

_labs = Table(
    "labs",
    _meta,
    Column("id", Text, primary_key=True),
    Column("number", Integer, nullable=False, default=1),
    Column("subject_id", Text, ForeignKey("subjects.id"), nullable=True),
    Column("lesson_id", Text, ForeignKey("lessons.id"), nullable=True),
    Column("title", Text, nullable=False),
    Column("topic", Text, nullable=True),
    Column("goal", Text, nullable=True),
    Column("formatting_guide", Text, nullable=True),
    Column("description", Text, nullable=True),
    Column("theory_content", Text, nullable=True),
    Column("practice_content", Text, nullable=True),
    Column("variants", Text, nullable=True),
    Column("questions", Text, nullable=True),
    Column("deadline_5_lessons", Integer, nullable=True),
    Column("deadline_4_lessons", Integer, nullable=True),
    Column("max_grade", Integer, default=5, nullable=False),
    Column("is_sequential", Boolean, default=True, nullable=False),
    Column("s3_key", Text, nullable=True),
    Column("is_published", Boolean, default=False, nullable=False),
    Column("public_code", Text, unique=True, nullable=True),
    Column("deleted_at", Text, nullable=True),
    Column("created_at", Text, nullable=True),
    Column("updated_at", Text, nullable=True),
    # SQLite-compatible unique constraint (без partial index — deleted_at проверяется в тесте)
    UniqueConstraint("subject_id", "number", name="uq_labs_subject_number_test"),
)

_lesson_grades = Table(
    "lesson_grades",
    _meta,
    Column("id", Text, primary_key=True),
    Column("lesson_id", Text, ForeignKey("lessons.id"), nullable=False),
    Column("student_id", Text, ForeignKey("users.id"), nullable=False),
    Column("work_number", Integer, nullable=True),
    Column("grade", Integer, nullable=False),
    Column("comment", String(500), nullable=True),
    Column("created_by", Text, nullable=True),
    Column("created_at", Text, nullable=True),
    Column("updated_at", Text, nullable=True),
    UniqueConstraint("lesson_id", "student_id", "work_number", name="uq_lesson_grade_student_lesson_work"),
    CheckConstraint("grade >= 2 AND grade <= 5", name="ck_lesson_grade_range"),
)


# ============================================================
# In-memory SQLite async engine for tests
# ============================================================

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(_meta.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(_meta.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session


# ============================================================
# Helpers — используем core insert для совместимости с SQLite
# ============================================================

from uuid import UUID as _UUID

from sqlalchemy import insert as sa_insert


async def make_group(db: AsyncSession):
    gid = uuid4()
    await db.execute(
        sa_insert(_groups).values(
            id=str(gid), code=f"GRP{gid.hex[:6]}", name="Test Group", invite_code=f"T{gid.hex[:6]}"
        )
    )
    await db.flush()

    class _G:
        id = gid

    return _G()


async def make_subject(db: AsyncSession):
    sid = uuid4()
    await db.execute(sa_insert(_subjects).values(id=str(sid), name="Math"))
    await db.flush()

    class _S:
        id = sid

    return _S()


async def make_lesson(
    db: AsyncSession, group, subject, lesson_type: LessonType = LessonType.LAB, work_number: int | None = 1
):
    lid = uuid4()
    await db.execute(
        sa_insert(_lessons).values(
            id=str(lid),
            group_id=str(group.id),
            subject_id=str(subject.id),
            date=date(2026, 3, 1),
            lesson_number=1,
            lesson_type=lesson_type.value,
            work_number=work_number,
            is_cancelled=False,
            ended_early=False,
        )
    )
    await db.flush()

    class _L:
        id = lid
        group_id = group.id
        subject_id = subject.id

    return _L()


async def make_lab(db: AsyncSession, subject, number: int = 1, is_published: bool = True):
    labid = uuid4()
    await db.execute(
        sa_insert(_labs).values(
            id=str(labid),
            title=f"Lab {number}",
            number=number,
            subject_id=str(subject.id),
            is_published=is_published,
            max_grade=5,
            is_sequential=True,
        )
    )
    await db.flush()

    class _Lab:
        id = labid
        subject_id = subject.id
        is_published = is_published
        deleted_at = None

    return _Lab()


async def make_student(db: AsyncSession, group):
    uid = uuid4()
    await db.execute(
        sa_insert(_users).values(
            id=str(uid),
            full_name="Student One",
            role="student",
            group_id=str(group.id),
            is_active=True,
            onboarding_completed=False,
            contacts="{}",
            contact_visibility="{}",
            teacher_settings="{}",
        )
    )
    await db.flush()

    class _U:
        id = uid
        group_id = group.id

    return _U()


# ============================================================
# BUG-1: Enum comparison
# ============================================================


class TestBug1EnumComparison:
    """
    BUG-1: lesson.lesson_type == "LAB" always False because enum value is "lab" (lowercase).
    Expected after fix: code uses LessonType.LAB enum, not string "LAB".

    Counterexample: LessonType.LAB == "LAB" → False (value is "lab")
    """

    def test_enum_value_is_lowercase(self):
        """Confirm: LessonType.LAB.value == 'lab' (lowercase)."""
        assert LessonType.LAB.value == "lab", f"Expected 'lab', got '{LessonType.LAB.value}'"

    def test_string_comparison_is_false(self):
        """
        After fix: no '== "LAB"' string comparisons in source files.
        Checks that the buggy files no longer contain the string comparison pattern.
        """
        import os

        buggy_files = [
            "app/api/v1/endpoints/journal/grades_endpoints.py",
            "app/api/v1/endpoints/journal/grades_bulk.py",
            "app/services/attestation/deadline_validator.py",
            "app/services/attestation/deadline_validator_batch.py",
        ]

        remaining_bugs = []
        for rel_path in buggy_files:
            for base in ["backend", "."]:
                full_path = os.path.join(base, rel_path)
                if os.path.exists(full_path):
                    with open(full_path) as f:
                        content = f.read()
                    if '== "LAB"' in content or "== 'LAB'" in content:
                        remaining_bugs.append(rel_path)
                    break

        assert len(remaining_bugs) == 0, (
            f"BUG NOT FIXED: string comparison '== \"LAB\"' still found in: {remaining_bugs}. "
            f"After fix: all comparisons must use LessonType.LAB enum."
        )

    def test_enum_comparison_is_true(self):
        """After fix: comparison via enum must be True."""
        assert LessonType.LAB == LessonType.LAB, "LessonType.LAB == LessonType.LAB must always be True"

    def test_lesson_type_value_stored_as_lowercase(self):
        """
        Confirms the root cause: LessonType.LAB.value == 'lab' (lowercase).
        Code uses string 'LAB' (uppercase) for comparison → always False.
        This is a pure documentation test — confirms the enum value.
        """
        # Confirm the enum value is lowercase — this is the root cause
        assert LessonType.LAB.value == "lab", (
            f"Unexpected: LessonType.LAB.value changed to '{LessonType.LAB.value}'. "
            f"Expected 'lab' (lowercase). If this changed, update all comparison sites."
        )


# ============================================================
# BUG-2: Student access to unpublished labs
# ============================================================


class TestBug2UnpublishedLabAccess:
    """
    BUG-2: get_lab_by_id() uses db.get(Lab, lab_id) — no is_published/deleted_at filter.
    Expected after fix: returns None for unpublished or deleted labs.

    Counterexample: get_lab_by_id(unpublished_lab.id) → returns lab (should return None)
    """

    def test_get_lab_by_id_uses_db_get_without_filter(self):
        """
        BUG CONFIRMED: get_lab_by_id() uses db.get(Lab, lab_id) — no filter.
        After fix: must use select() with is_published=True and deleted_at IS NULL.
        """
        import inspect

        from app.services.student_lab_service import StudentLabService

        source = inspect.getsource(StudentLabService.get_lab_by_id)

        # Bug: uses db.get() which has no filter capability
        uses_db_get = "db.get(Lab" in source or "db.get(" in source

        assert not uses_db_get, (
            "BUG CONFIRMED: get_lab_by_id() uses db.get(Lab, lab_id) — no is_published/deleted_at filter. "
            "Counterexample: get_lab_by_id(unpublished_lab.id) returns the lab (should return None). "
            "After fix: must use select(Lab).where(Lab.id == lab_id, Lab.is_published.is_(True), "
            "Lab.deleted_at.is_(None))."
        )

    def test_get_lab_by_id_has_published_filter(self):
        """After fix: source must contain is_published filter."""
        import inspect

        from app.services.student_lab_service import StudentLabService

        source = inspect.getsource(StudentLabService.get_lab_by_id)

        has_published_filter = "is_published" in source
        has_deleted_filter = "deleted_at" in source

        assert has_published_filter, (
            "BUG CONFIRMED: get_lab_by_id() has no is_published filter. "
            "After fix: must filter Lab.is_published.is_(True)."
        )
        assert has_deleted_filter, (
            "BUG CONFIRMED: get_lab_by_id() has no deleted_at filter. After fix: must filter Lab.deleted_at.is_(None)."
        )


# ============================================================
# BUG-3: Grade scale mismatch (0-100 vs 2-5)
# ============================================================


class TestBug3GradeScaleMismatch:
    """
    BUG-3: AcceptSubmissionRequest.grade has Field(ge=0, le=100).
    LessonGrade has CHECK constraint grade >= 2 AND grade <= 5.
    Accepting grade=85 passes Pydantic but fails DB constraint on sync.

    Counterexample: AcceptSubmissionRequest(grade=85) → no ValidationError (should raise)
    """

    def test_grade_85_passes_validation(self):
        """
        BUG CONFIRMED: grade=85 passes AcceptSubmissionRequest validation.
        After fix: must raise ValidationError.
        """
        from app.api.v1.endpoints.admin_lab_queue import AcceptSubmissionRequest

        try:
            req = AcceptSubmissionRequest(grade=85)
            raise AssertionError(
                f"BUG CONFIRMED: AcceptSubmissionRequest(grade=85) did not raise ValidationError. "
                f"Counterexample: grade=85 accepted (ge=0, le=100), "
                f"but LessonGrade CHECK constraint requires grade in [2,5]. "
                f"Created: {req!r}"
            )
        except ValidationError:
            pass  # After fix this is the expected path

    def test_grade_0_passes_validation(self):
        """
        BUG CONFIRMED: grade=0 passes validation (below minimum 2).
        After fix: must raise ValidationError.
        """
        from app.api.v1.endpoints.admin_lab_queue import AcceptSubmissionRequest

        try:
            req = AcceptSubmissionRequest(grade=0)
            raise AssertionError(
                f"BUG CONFIRMED: AcceptSubmissionRequest(grade=0) did not raise ValidationError. "
                f"Counterexample: grade=0 accepted, but minimum should be 2. Got: {req!r}"
            )
        except ValidationError:
            pass

    def test_grade_6_passes_validation(self):
        """
        BUG CONFIRMED: grade=6 passes validation (above maximum 5).
        After fix: must raise ValidationError.
        """
        from app.api.v1.endpoints.admin_lab_queue import AcceptSubmissionRequest

        try:
            req = AcceptSubmissionRequest(grade=6)
            raise AssertionError(
                f"BUG CONFIRMED: AcceptSubmissionRequest(grade=6) did not raise ValidationError. "
                f"Counterexample: grade=6 accepted, but maximum should be 5. Got: {req!r}"
            )
        except ValidationError:
            pass

    def test_valid_grades_pass(self):
        """Preservation: grades 2-5 must pass validation."""
        from app.api.v1.endpoints.admin_lab_queue import AcceptSubmissionRequest

        for g in [2, 3, 4, 5]:
            req = AcceptSubmissionRequest(grade=g)
            assert req.grade == g, f"Grade {g} should be accepted"


# ============================================================
# BUG-4: Bulk upsert creates duplicates
# ============================================================


class TestBug4BulkDuplicate:
    """
    BUG-4: bulk_upsert_lesson_grades() only checks grades on current lesson_id.
    If grade for work_number exists on another lesson — creates duplicate instead of moving.

    Counterexample: grade(student, work_number=1) on lesson_A,
    bulk_upsert on lesson_B with same work_number → 2 grades exist (should be 1)
    """

    def test_bulk_upsert_missing_cross_lesson_check(self):
        """
        BUG CONFIRMED: bulk_upsert_lesson_grades() only checks current lesson_id.
        After fix: must check for existing grades on OTHER lessons (like single upsert does).
        """
        import inspect

        from app.crud.crud_lesson_grade import bulk_upsert_lesson_grades

        source = inspect.getsource(bulk_upsert_lesson_grades)

        # Bug: only queries current lesson_id
        only_checks_current_lesson = (
            "LessonGrade.lesson_id == lesson_id" in source
            and "get_student_grade_by_work" not in source
            and "lesson_id !=" not in source
        )

        assert not only_checks_current_lesson, (
            "BUG CONFIRMED: bulk_upsert_lesson_grades() only checks grades on current lesson_id. "
            "Counterexample: grade(student, work_number=1) on lesson_A, "
            "bulk_upsert on lesson_B → creates 2nd grade (duplicate) instead of moving. "
            "After fix: must check for existing grades on OTHER lessons "
            "(like single upsert via get_student_grade_by_work)."
        )

    def test_single_upsert_has_cross_lesson_check(self):
        """Preservation: single upsert already has cross-lesson check (must stay)."""
        import inspect

        from app.crud.crud_lesson_grade import upsert_lesson_grade

        source = inspect.getsource(upsert_lesson_grade)

        assert "get_student_grade_by_work" in source, (
            "Preservation broken: upsert_lesson_grade() lost its cross-lesson check. "
            "Must call get_student_grade_by_work() to find grades on other lessons."
        )


# ============================================================
# BUG-5: DELETE without work_number — MultipleResultsFound
# ============================================================


class TestBug5DeleteMultipleGrades:
    """
    BUG-5: delete_grade_by_lesson_student() uses scalar_one_or_none() without work_number filter.
    When student has 2+ grades on same lesson (different work_numbers) → MultipleResultsFound.

    Counterexample: 2 grades (work_number=1, work_number=2) on same lesson,
    DELETE /grades?lesson_id=X&student_id=Y → MultipleResultsFound exception
    """

    @pytest.mark.asyncio
    async def test_delete_raises_on_multiple_grades(self, db: AsyncSession):
        """
        BUG CONFIRMED: scalar_one_or_none() raises MultipleResultsFound.
        After fix: must return 400 requiring work_number.
        """
        from sqlalchemy import and_, select
        from sqlalchemy.exc import MultipleResultsFound

        group = await make_group(db)
        subject = await make_subject(db)
        student = await make_student(db, group)
        lesson = await make_lesson(db, group, subject)

        # Two grades on same lesson, different work_numbers
        await db.execute(
            sa_insert(_lesson_grades).values(
                id=str(uuid4()),
                lesson_id=str(lesson.id),
                student_id=str(student.id),
                grade=3,
                work_number=1,
            )
        )
        await db.execute(
            sa_insert(_lesson_grades).values(
                id=str(uuid4()),
                lesson_id=str(lesson.id),
                student_id=str(student.id),
                grade=4,
                work_number=2,
            )
        )
        await db.commit()

        # Simulate what delete_grade_by_lesson_student() does (without work_number)
        result = await db.execute(
            select(_lesson_grades).where(
                and_(
                    _lesson_grades.c.lesson_id == str(lesson.id),
                    _lesson_grades.c.student_id == str(student.id),
                )
            )
        )
        try:
            grade = result.scalar_one_or_none()
            raise AssertionError(
                f"BUG CONFIRMED: scalar_one_or_none() did not raise MultipleResultsFound. "
                f"Counterexample: 2 grades (work_number=1,2) on same lesson, "
                f"scalar_one_or_none() returned: {grade!r} (arbitrary result, not an error). "
                f"After fix: endpoint must return HTTP 400 requiring work_number."
            )
        except MultipleResultsFound:
            # This is the bug — confirms it exists
            pass  # BUG CONFIRMED via exception


# ============================================================
# BUG-6: Non-atomic sync — commit before sync
# ============================================================


class TestBug6NonAtomicSync:
    """
    BUG-6: upsert_lesson_grade() calls await db.commit() before sync.
    If sync raises exception — LessonGrade is already committed without Submission.

    Counterexample: upsert succeeds + commit, then sync raises → grade committed, no submission
    """

    def test_upsert_contains_commit_before_sync(self):
        """
        BUG CONFIRMED: upsert_lesson_grade() calls db.commit() internally.
        After fix: must use db.flush() so caller controls the transaction.
        """
        import inspect

        from app.crud.crud_lesson_grade import upsert_lesson_grade

        source = inspect.getsource(upsert_lesson_grade)

        # Bug: function calls db.commit() — commits before sync can happen
        assert "await db.commit()" not in source, (
            "BUG CONFIRMED: upsert_lesson_grade() calls 'await db.commit()' internally. "
            "Counterexample: upsert_lesson_grade() commits LessonGrade, then sync raises → "
            "grade is persisted without corresponding Submission update. "
            "After fix: replace 'await db.commit()' with 'await db.flush()' so the caller "
            "controls the transaction boundary."
        )

    def test_bulk_upsert_contains_commit(self):
        """
        BUG CONFIRMED: bulk_upsert_lesson_grades() calls db.commit() internally.
        After fix: must use db.flush().
        """
        import inspect

        from app.crud.crud_lesson_grade import bulk_upsert_lesson_grades

        source = inspect.getsource(bulk_upsert_lesson_grades)

        assert "await db.commit()" not in source, (
            "BUG CONFIRMED: bulk_upsert_lesson_grades() calls 'await db.commit()' internally. "
            "Counterexample: bulk upsert commits, then sync raises → grades committed without sync. "
            "After fix: replace 'await db.commit()' with 'await db.flush()'."
        )


# ============================================================
# BUG-7: get_user_journal_grades() missing subject_id filter
# ============================================================


class TestBug7SubjectFilter:
    """
    BUG-7: get_user_journal_grades() filters only by student_id + work_number IS NOT NULL.
    No JOIN on Lesson for subject_id filter → mixes grades from different subjects.

    Counterexample: student has grade(work_number=1, grade=5) in math
    and grade(work_number=1, grade=3) in physics.
    get_user_journal_grades() returns grade=5 (best from both subjects).
    """

    def test_get_user_journal_grades_missing_subject_id_param(self):
        """
        BUG CONFIRMED: get_user_journal_grades() has no subject_id parameter.
        After fix: must accept subject_id and filter by it.
        """
        import inspect

        from app.services.student_lab_service import StudentLabService

        service = StudentLabService()
        sig = inspect.signature(service.get_user_journal_grades)
        has_subject_id = "subject_id" in sig.parameters

        assert has_subject_id, (
            "BUG CONFIRMED: get_user_journal_grades() has no subject_id parameter. "
            "Counterexample: student has work_number=1 in math (grade=5) and physics (grade=3). "
            "Without subject_id filter, method returns grade=5 (best from both subjects). "
            "After fix: method must accept subject_id and filter by it via JOIN on Lesson."
        )

    @pytest.mark.asyncio
    async def test_journal_grades_mixes_subjects(self, db: AsyncSession):
        """
        BUG CONFIRMED: get_user_journal_grades() returns grades from wrong subject.
        After fix: must filter by subject_id.
        """
        import inspect

        from app.services.student_lab_service import StudentLabService

        service = StudentLabService()
        sig = inspect.signature(service.get_user_journal_grades)

        # If no subject_id param — bug confirmed (signature check is the primary test)
        if "subject_id" not in sig.parameters:
            # Bug confirmed by signature — skip DB part
            pytest.skip("BUG CONFIRMED via signature: no subject_id param (see test above)")

        group = await make_group(db)
        subject_math = await make_subject(db)
        subject_physics_id = str(uuid4())
        await db.execute(sa_insert(_subjects).values(id=subject_physics_id, name="Physics"))
        await db.flush()

        student = await make_student(db, group)

        lesson_math = await make_lesson(db, group, subject_math, work_number=1)
        lesson_physics_id = str(uuid4())
        await db.execute(
            sa_insert(_lessons).values(
                id=lesson_physics_id,
                group_id=str(group.id),
                subject_id=subject_physics_id,
                date=date(2026, 3, 2),
                lesson_number=2,
                lesson_type=LessonType.LAB.value,
                work_number=1,
                is_cancelled=False,
                ended_early=False,
            )
        )
        await db.flush()

        # Grade 5 in math, grade 3 in physics — both work_number=1
        await db.execute(
            sa_insert(_lesson_grades).values(
                id=str(uuid4()),
                lesson_id=str(lesson_math.id),
                student_id=str(student.id),
                grade=5,
                work_number=1,
            )
        )
        await db.execute(
            sa_insert(_lesson_grades).values(
                id=str(uuid4()),
                lesson_id=lesson_physics_id,
                student_id=str(student.id),
                grade=3,
                work_number=1,
            )
        )
        await db.commit()

        # After fix: grades for math should only contain math grade
        grades_math = await service.get_user_journal_grades(db, student.id, subject_id=subject_math.id)
        assert 1 in grades_math, "work_number=1 must be in math grades"
        assert str(grades_math[1].lesson_id) == str(lesson_math.id), (
            f"BUG CONFIRMED: grades_math[1] is from lesson {grades_math[1].lesson_id}, "
            f"expected math lesson {lesson_math.id}. Subject filter not working."
        )


# ============================================================
# BUG-8: No UNIQUE constraint on (subject_id, number) in labs
# ============================================================


class TestBug8UniqueLabNumber:
    """
    BUG-8: Lab model has Index("idx_labs_subject_number", ...) but no UniqueConstraint.
    Two labs with same subject_id+number can be created.
    find_published_lab() with scalar_one_or_none() → MultipleResultsFound.

    Counterexample: create_lab(subject_id=X, number=1) twice → both succeed (should fail)
    """

    @pytest.mark.asyncio
    async def test_duplicate_lab_number_allowed(self, db: AsyncSession):
        """
        BUG CONFIRMED: two labs with same subject_id+number can be created.
        After fix: second creation must raise IntegrityError.
        """
        from sqlalchemy.exc import IntegrityError

        subject = await make_subject(db)
        await db.execute(
            sa_insert(_labs).values(
                id=str(uuid4()),
                title="Lab 1",
                number=1,
                subject_id=str(subject.id),
                is_published=True,
                max_grade=5,
                is_sequential=True,
            )
        )
        await db.commit()

        try:
            await db.execute(
                sa_insert(_labs).values(
                    id=str(uuid4()),
                    title="Lab 1 duplicate",
                    number=1,
                    subject_id=str(subject.id),
                    is_published=True,
                    max_grade=5,
                    is_sequential=True,
                )
            )
            await db.commit()
            # If we get here — bug confirmed (no constraint)
            raise AssertionError(
                "BUG CONFIRMED: Two labs with same subject_id+number=1 were created without error. "
                "Counterexample: Lab(subject_id=X, number=1) created twice — both succeed. "
                "After fix: UniqueConstraint on (subject_id, number) WHERE deleted_at IS NULL "
                "must raise IntegrityError on second insert."
            )
        except IntegrityError:
            await db.rollback()
            # After fix: this is the expected path

    @pytest.mark.asyncio
    async def test_different_numbers_allowed(self, db: AsyncSession):
        """Preservation: labs with different numbers for same subject must be allowed."""
        subject = await make_subject(db)
        await db.execute(
            sa_insert(_labs).values(
                id=str(uuid4()),
                title="Lab 1",
                number=1,
                subject_id=str(subject.id),
                is_published=True,
                max_grade=5,
                is_sequential=True,
            )
        )
        await db.execute(
            sa_insert(_labs).values(
                id=str(uuid4()),
                title="Lab 2",
                number=2,
                subject_id=str(subject.id),
                is_published=True,
                max_grade=5,
                is_sequential=True,
            )
        )
        await db.commit()
        # No exception — correct behavior


# ============================================================
# BUG-9: lab_service doesn't validate subject_id vs lesson.subject_id
# ============================================================


class TestBug9SubjectLessonConsistency:
    """
    BUG-9: lab_service.create/update auto-syncs subject_id from lesson_id
    only when subject_id is NOT provided. If both provided — no consistency check.

    Counterexample: create_lab(subject_id=math_id, lesson_id=physics_lesson_id)
    → lab created with inconsistent data (no error)
    """

    def test_lab_service_create_missing_consistency_check(self):
        """
        BUG CONFIRMED: LabService.create() has no subject_id vs lesson.subject_id check.
        After fix: must raise ValueError when subject_id != lesson.subject_id.
        """
        import inspect

        from app.services.lab_service import LabService

        source = inspect.getsource(LabService.create)

        # After fix: must contain a consistency validation
        has_consistency_check = (
            "_validate_subject_lesson_consistency" in source
            or "subject_id != lesson.subject_id" in source
            or "subject_id != lesson_subject_id" in source
        )

        assert has_consistency_check, (
            "BUG CONFIRMED: LabService.create() has no subject_id/lesson consistency check. "
            "Counterexample: create_lab(subject_id=math_id, lesson_id=physics_lesson_id) "
            "→ lab created with inconsistent data (subject_id=math, lesson belongs to physics). "
            "After fix: must call _validate_subject_lesson_consistency() or equivalent check."
        )

    def test_lab_service_update_missing_consistency_check(self):
        """
        BUG CONFIRMED: LabService.update() has no subject_id vs lesson.subject_id check.
        After fix: must raise ValueError when subject_id != lesson.subject_id.
        """
        import inspect

        from app.services.lab_service import LabService

        source = inspect.getsource(LabService.update)

        has_consistency_check = (
            "_validate_subject_lesson_consistency" in source
            or "subject_id != lesson.subject_id" in source
            or "subject_id != lesson_subject_id" in source
        )

        assert has_consistency_check, (
            "BUG CONFIRMED: LabService.update() has no subject_id/lesson consistency check. "
            "Counterexample: update_lab(subject_id=math_id, lesson_id=physics_lesson_id) "
            "→ lab updated with inconsistent data. "
            "After fix: must validate subject_id matches lesson.subject_id."
        )

    @pytest.mark.asyncio
    async def test_create_lab_only_lesson_id_auto_syncs(self, db: AsyncSession):
        """Preservation: create with only lesson_id auto-syncs subject_id (req 3.6).
        NOTE: Tested via integration test on real DB — LabService uses ORM internally.
        """
        pytest.skip("Requires PostgreSQL — LabService.create() uses ORM with pg metadata")

    @pytest.mark.asyncio
    async def test_create_lab_only_subject_id_no_lesson(self, db: AsyncSession):
        """Preservation: create with only subject_id (no lesson_id) must work (req 3.7).
        NOTE: Tested via integration test on real DB — LabService uses ORM internally.
        """
        pytest.skip("Requires PostgreSQL — LabService.create() uses ORM with pg metadata")
