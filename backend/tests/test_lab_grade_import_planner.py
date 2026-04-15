from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.lab_grade_import import planner as planner_module
from app.services.lab_grade_import.planner import LabGradeImportPlanner
from app.services.lab_grade_import.types import ImportPlan, ParsedGradeEntry, PlannedGradeWrite


def make_entry(work_number: int) -> ParsedGradeEntry:
    return ParsedGradeEntry(
        source_date=date(2026, 4, 15),
        group_label="238",
        student_label="Боброва",
        grade=5,
        work_number=work_number,
        raw_line="Боброва - 5(8)",
        line_number=10,
    )


def make_write(entry: ParsedGradeEntry, *, lesson_id=None) -> PlannedGradeWrite:
    return PlannedGradeWrite(
        entry=entry,
        student_id=uuid4(),
        student_name="Боброва Анна",
        group_id=uuid4(),
        group_name="ИС1-238",
        subject_id=uuid4(),
        lab_id=uuid4(),
        lesson_id=lesson_id or uuid4(),
        lesson_date=date(2026, 4, 15),
        lesson_number=2,
    )


@pytest.mark.asyncio
async def test_build_plan_rejects_duplicate_source_work(monkeypatch):
    planner = LabGradeImportPlanner()
    entry = make_entry(8)
    write = make_write(entry)

    async def fake_plan_entry(db, planned_entry, plan):
        return PlannedGradeWrite(
            entry=planned_entry,
            student_id=write.student_id,
            student_name=write.student_name,
            group_id=write.group_id,
            group_name=write.group_name,
            subject_id=write.subject_id,
            lab_id=write.lab_id,
            lesson_id=write.lesson_id,
            lesson_date=write.lesson_date,
            lesson_number=write.lesson_number,
        )

    monkeypatch.setattr(planner, "_plan_entry", fake_plan_entry)

    plan = await planner.build_plan(db=None, entries=[entry, entry])

    assert len(plan.planned) == 1
    assert [issue.code for issue in plan.issues] == ["duplicate_source_work"]


@pytest.mark.asyncio
async def test_build_plan_rejects_two_works_on_same_lesson(monkeypatch):
    planner = LabGradeImportPlanner()
    first = make_entry(7)
    second = make_entry(8)
    lesson_id = uuid4()
    first_write = make_write(first, lesson_id=lesson_id)
    second_write = PlannedGradeWrite(
        entry=second,
        student_id=first_write.student_id,
        student_name=first_write.student_name,
        group_id=first_write.group_id,
        group_name=first_write.group_name,
        subject_id=uuid4(),
        lab_id=uuid4(),
        lesson_id=lesson_id,
        lesson_date=first_write.lesson_date,
        lesson_number=first_write.lesson_number,
    )

    async def fake_plan_entry(db, planned_entry, plan):
        return first_write if planned_entry.work_number == 7 else second_write

    monkeypatch.setattr(planner, "_plan_entry", fake_plan_entry)

    plan = await planner.build_plan(db=None, entries=[first, second])

    assert len(plan.planned) == 1
    assert [issue.code for issue in plan.issues] == ["source_cell_conflict"]


@pytest.mark.asyncio
async def test_plan_entry_does_not_drop_old_source_date_before_lesson_lookup(monkeypatch):
    planner = LabGradeImportPlanner(start_date=date(2026, 3, 13))
    entry = ParsedGradeEntry(
        source_date=date(2025, 6, 24),
        group_label="235",
        student_label="Бурёнкина",
        grade=5,
        work_number=5,
        raw_line="Бурёнкина - 5-10 (5)",
        line_number=20,
    )
    student = SimpleNamespace(id=uuid4(), full_name="Буренкина Камила Алексеевна", subgroup=1)
    group = SimpleNamespace(id=uuid4(), name="ИС1-235-ОТ")
    lesson = SimpleNamespace(id=uuid4(), subject_id=uuid4(), date=date(2026, 3, 20), lesson_number=2)
    lab = SimpleNamespace(id=uuid4())

    async def fake_resolve_student_group(*args, **kwargs):
        return student, group

    async def fake_resolve_target(*args, **kwargs):
        return lesson, lab

    async def false_check(*args, **kwargs):
        return False

    async def max_grade(*args, **kwargs):
        return 5

    monkeypatch.setattr(planner, "_resolve_student_group", fake_resolve_student_group)
    monkeypatch.setattr(planner, "_resolve_target_lesson_and_lab", fake_resolve_target)
    monkeypatch.setattr(planner, "_has_existing_work_grade", false_check)
    monkeypatch.setattr(planner, "_has_other_grade_on_lesson", false_check)
    monkeypatch.setattr(planner_module, "get_max_allowed_grade", max_grade)

    write = await planner._plan_entry(db=None, entry=entry, plan=ImportPlan())

    assert write is not None
    assert write.student_name == "Буренкина Камила Алексеевна"


@pytest.mark.asyncio
async def test_plan_entry_uses_student_database_group_when_source_group_missing(monkeypatch):
    planner = LabGradeImportPlanner(start_date=date(2026, 3, 13))
    student_id = uuid4()
    group_id = uuid4()
    lesson_id = uuid4()
    subject_id = uuid4()
    lab_id = uuid4()
    student = SimpleNamespace(id=student_id, full_name="Висягина Мирра Андреевна", subgroup=1)
    group = SimpleNamespace(id=group_id, name="ИС1-235-ОТ")
    lesson = SimpleNamespace(
        id=lesson_id,
        subject_id=subject_id,
        date=date(2026, 3, 20),
        lesson_number=2,
    )
    lab = SimpleNamespace(id=lab_id)
    entry = ParsedGradeEntry(
        source_date=date(2026, 3, 20),
        group_label=None,
        student_label="Висягина",
        grade=5,
        work_number=5,
        raw_line="Висягина - 5(5)",
        line_number=15,
    )

    async def fake_resolve_student_group(db, planned_entry):
        assert planned_entry is entry
        return student, group

    async def fake_resolve_target(db, resolved_group, resolved_student, work_number):
        assert resolved_group is group
        assert resolved_student is student
        assert work_number == 5
        return lesson, lab

    async def false_check(*args, **kwargs):
        return False

    async def max_grade(*args, **kwargs):
        return 5

    monkeypatch.setattr(planner, "_resolve_student_group", fake_resolve_student_group)
    monkeypatch.setattr(planner, "_resolve_target_lesson_and_lab", fake_resolve_target)
    monkeypatch.setattr(planner, "_has_existing_work_grade", false_check)
    monkeypatch.setattr(planner, "_has_other_grade_on_lesson", false_check)
    monkeypatch.setattr(planner_module, "get_max_allowed_grade", max_grade)

    write = await planner._plan_entry(db=None, entry=entry, plan=ImportPlan())

    assert write is not None
    assert write.student_id == student_id
    assert write.group_id == group_id
    assert write.group_name == "ИС1-235-ОТ"


@pytest.mark.asyncio
async def test_plan_entry_keeps_existing_grade_read_only(monkeypatch):
    planner = LabGradeImportPlanner(start_date=date(2026, 3, 13))
    student = SimpleNamespace(id=uuid4(), full_name="Буренкина Камила Алексеевна", subgroup=1)
    group = SimpleNamespace(id=uuid4(), name="ИС1-235-ОТ")
    lesson = SimpleNamespace(id=uuid4(), subject_id=uuid4(), date=date(2026, 3, 20), lesson_number=2)
    lab = SimpleNamespace(id=uuid4())
    entry = ParsedGradeEntry(
        source_date=date(2026, 3, 20),
        group_label=None,
        student_label="Бурёнкина",
        grade=5,
        work_number=5,
        raw_line="Бурёнкина - 5-10 (5)",
        line_number=16,
    )
    plan = ImportPlan()

    async def fake_resolve_student_group(db, planned_entry):
        return student, group

    async def fake_resolve_target(*args, **kwargs):
        return lesson, lab

    async def has_existing_grade(*args, **kwargs):
        return True

    monkeypatch.setattr(planner, "_resolve_student_group", fake_resolve_student_group)
    monkeypatch.setattr(planner, "_resolve_target_lesson_and_lab", fake_resolve_target)
    monkeypatch.setattr(planner, "_has_existing_work_grade", has_existing_grade)

    write = await planner._plan_entry(db=None, entry=entry, plan=plan)

    assert write is None
    assert [issue.code for issue in plan.issues] == ["existing_grade"]


@pytest.mark.asyncio
async def test_plan_entry_allows_journal_only_grade_without_lab_record(monkeypatch):
    planner = LabGradeImportPlanner(start_date=date(2026, 3, 13))
    student = SimpleNamespace(id=uuid4(), full_name="Висягина Мирра Андреевна", subgroup=1)
    group = SimpleNamespace(id=uuid4(), name="ИС1-235-ОТ")
    lesson = SimpleNamespace(id=uuid4(), subject_id=uuid4(), date=date(2026, 4, 17), lesson_number=1)
    entry = ParsedGradeEntry(
        source_date=date(2026, 3, 20),
        group_label=None,
        student_label="Висягина",
        grade=5,
        work_number=5,
        raw_line="Висягина - 5(5)",
        line_number=15,
    )

    async def fake_resolve_student_group(db, planned_entry):
        return student, group

    async def fake_resolve_target(*args, **kwargs):
        return lesson, None

    async def false_check(*args, **kwargs):
        return False

    async def max_grade(*args, **kwargs):
        return 5

    monkeypatch.setattr(planner, "_resolve_student_group", fake_resolve_student_group)
    monkeypatch.setattr(planner, "_resolve_target_lesson_and_lab", fake_resolve_target)
    monkeypatch.setattr(planner, "_has_existing_work_grade", false_check)
    monkeypatch.setattr(planner, "_has_other_grade_on_lesson", false_check)
    monkeypatch.setattr(planner_module, "get_max_allowed_grade", max_grade)

    write = await planner._plan_entry(db=None, entry=entry, plan=ImportPlan())

    assert write is not None
    assert write.lab_id is None
