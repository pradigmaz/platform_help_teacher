"""Shared attendance contract helpers for reports, attestation, and export."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from app.models.attendance import Attendance, AttendanceStatus
from app.models.lesson import Lesson
from app.models.user import User
from app.services.attendance_slots import LessonSlot, get_lesson_slot_sets

AttendanceValueMap = dict[str, int | float]


def _record_key(record: Attendance) -> LessonSlot:
    return (record.date, record.lesson_number)


def lesson_key(lesson: Lesson) -> str:
    return f"{lesson.date}_{lesson.lesson_number}"


@dataclass(slots=True)
class AttendanceCounts:
    present: int = 0
    late: int = 0
    excused: int = 0
    absent: int = 0

    @property
    def total(self) -> int:
        return self.present + self.late + self.excused + self.absent

    @classmethod
    def from_statuses(cls, statuses: Iterable[AttendanceStatus | None]) -> AttendanceCounts:
        counts = cls()
        for status in statuses:
            if status == AttendanceStatus.PRESENT:
                counts.present += 1
            elif status == AttendanceStatus.LATE:
                counts.late += 1
            elif status == AttendanceStatus.EXCUSED:
                counts.excused += 1
            elif status == AttendanceStatus.ABSENT:
                counts.absent += 1
        return counts

    @classmethod
    def from_records(
        cls,
        records: Iterable[Attendance],
        transfer_counts: Mapping[str, int] | None = None,
    ) -> AttendanceCounts:
        counts = cls.from_statuses(record.status for record in records)
        if transfer_counts:
            counts.present += int(transfer_counts.get("present", 0))
            counts.late += int(transfer_counts.get("late", 0))
            counts.excused += int(transfer_counts.get("excused", 0))
            counts.absent += int(transfer_counts.get("absent", 0))
        return counts


@dataclass(slots=True)
class StudentAttendanceSnapshot:
    expected_lessons: int
    counts: AttendanceCounts
    statuses_by_lesson_key: dict[str, AttendanceStatus] = field(default_factory=dict)

    def report_rate(self) -> float:
        return calculate_report_attendance_rate(self.counts, self.expected_lessons)


def calculate_report_attendance_rate(counts: AttendanceCounts, expected_lessons: int) -> float:
    """Presentation metric for reports and export within a fixed lesson set."""
    if expected_lessons <= 0:
        return 0.0
    if counts.excused == expected_lessons and counts.present == 0 and counts.late == 0 and counts.absent == 0:
        return 100.0
    present_equivalent = counts.present + counts.late * 0.5 + counts.excused * 0.5
    return round(min(present_equivalent / expected_lessons * 100, 100.0), 1)


def calculate_lesson_attendance_rate(*, present_count: int, late_count: int, total_count: int) -> float:
    """Lesson-level attendance metric for report history/timeline."""
    if total_count <= 0:
        return 0.0
    return round((present_count + late_count) / total_count * 100, 1)


def snapshot_to_report_stats(snapshot: StudentAttendanceSnapshot | None) -> AttendanceValueMap:
    """Convert a normalized student snapshot into the public report/export payload."""
    if snapshot is None:
        return {"present": 0, "late": 0, "excused": 0, "absent": 0, "total": 0, "rate": 0.0}
    return {
        "present": snapshot.counts.present,
        "late": snapshot.counts.late,
        "excused": snapshot.counts.excused,
        "absent": snapshot.counts.absent,
        "total": snapshot.expected_lessons,
        "rate": snapshot.report_rate(),
    }


def build_student_attendance_snapshots(
    *,
    students: Iterable[User],
    lessons: Iterable[Lesson],
    attendance_records: Iterable[Attendance],
) -> dict[UUID, StudentAttendanceSnapshot]:
    """Normalize attendance into per-student lesson snapshots."""
    lesson_list = list(lessons)
    attendance_by_student: dict[UUID, list[Attendance]] = defaultdict(list)
    for record in attendance_records:
        attendance_by_student[record.student_id].append(record)

    common_lessons = [lesson for lesson in lesson_list if lesson.subgroup is None]
    subgroup_lessons: dict[int, list[Lesson]] = defaultdict(list)
    for lesson in lesson_list:
        if lesson.subgroup is not None:
            subgroup_lessons[lesson.subgroup].append(lesson)

    snapshots: dict[UUID, StudentAttendanceSnapshot] = {}
    for student in students:
        relevant_lessons = list(common_lessons)
        if student.subgroup is not None:
            relevant_lessons.extend(subgroup_lessons.get(student.subgroup, ()))

        key_by_id = {lesson.id: lesson_key(lesson) for lesson in relevant_lessons}
        key_by_slot = {(lesson.date, lesson.lesson_number): lesson_key(lesson) for lesson in relevant_lessons}
        statuses_by_lesson_key = {lesson_key(lesson): AttendanceStatus.ABSENT for lesson in relevant_lessons}
        lesson_ids, legacy_slots = get_lesson_slot_sets(relevant_lessons)

        for record in attendance_by_student.get(student.id, ()):
            record_slot = _record_key(record)
            if record.lesson_id is not None:
                target_key = key_by_id.get(record.lesson_id)
            elif record_slot in legacy_slots:
                target_key = key_by_slot.get(record_slot)
            else:
                target_key = None
            if target_key is not None:
                statuses_by_lesson_key[target_key] = record.status

        snapshots[student.id] = StudentAttendanceSnapshot(
            expected_lessons=len(relevant_lessons),
            counts=AttendanceCounts.from_statuses(statuses_by_lesson_key.values()),
            statuses_by_lesson_key=statuses_by_lesson_key,
        )

    return snapshots
