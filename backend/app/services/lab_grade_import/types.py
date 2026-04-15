"""Typed import plan objects for lab grade backfills."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class ParsedGradeEntry:
    source_date: date | None
    group_label: str | None
    student_label: str
    grade: int
    work_number: int
    raw_line: str
    line_number: int


@dataclass(frozen=True)
class ImportIssue:
    entry: ParsedGradeEntry
    code: str
    message: str


@dataclass(frozen=True)
class PlannedGradeWrite:
    entry: ParsedGradeEntry
    student_id: UUID
    student_name: str
    group_id: UUID
    group_name: str
    subject_id: UUID
    lab_id: UUID | None
    lesson_id: UUID
    lesson_date: date
    lesson_number: int


@dataclass
class ImportPlan:
    parsed: int = 0
    planned: list[PlannedGradeWrite] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)

    @property
    def skipped(self) -> int:
        return len(self.issues)
