"""Parse teacher date notes into normalized lab grade entries."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from app.services.lab_grade_import.types import ParsedGradeEntry

DATE_RE = re.compile(r"^(?:##\s+)?(?P<date>\d{2}\.\d{2}\.\d{2,4})(?:\s+(?P<tail>.+))?$")
GROUP_HEADER_RE = re.compile(r"^###\s+Группа\s+(?P<group>.+)$", re.IGNORECASE)
GROUP_LINE_RE = re.compile(r"^(?P<group>(?:ИС\d?-)?\d{3}|\d{3}(?:\s+ИС)?)$", re.IGNORECASE)
INLINE_GROUP_RE = re.compile(r"(?P<group>(?:ИС\d?-)?\d{3}|\d{3})", re.IGNORECASE)
GRADE_WORK_RE = re.compile(r"(?P<grade>[2-5])\s*\(\s*(?P<works>\d+(?:\s*-\s*\d+)?)\s*\)")
WORK_GRADE_RE = re.compile(r"(?P<works>\d+\s*-\s*\d+)\s*\(\s*(?P<grade>[2-5])\s*\)")


def parse_grade_notes(path: Path) -> list[ParsedGradeEntry]:
    current_date: date | None = None
    current_group: str | None = None
    entries: list[ParsedGradeEntry] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        date_match = DATE_RE.match(line)
        if date_match:
            current_date = _parse_date(date_match.group("date"))
            current_group = _clean_group(date_match.group("tail"))
            continue

        group_match = GROUP_HEADER_RE.match(line)
        if group_match:
            current_group = _clean_group(group_match.group("group"))
            continue
        if line.lower().startswith("### без указанной"):
            current_group = None
            continue
        if line.startswith("#"):
            continue

        raw_group_match = GROUP_LINE_RE.match(line)
        if raw_group_match:
            current_group = _clean_group(raw_group_match.group("group"))
            continue

        entries.extend(_parse_entry_line(line, current_date, current_group, line_number, raw_line))

    return entries


def _parse_entry_line(
    line: str, current_date: date | None, current_group: str | None, line_number: int, raw_line: str
) -> list[ParsedGradeEntry]:
    line = line.removeprefix("-").strip()
    if line.lower().startswith(("заметка:", "болела:")):
        return []

    matches = sorted(
        [*GRADE_WORK_RE.finditer(line), *WORK_GRADE_RE.finditer(line)],
        key=lambda match: match.start(),
    )
    if not matches:
        return []

    student_label, group_label = _extract_student_and_group(line[: matches[0].start()], current_group)
    if not student_label:
        return []

    entries: list[ParsedGradeEntry] = []
    for match in matches:
        for work_number in _expand_work_numbers(match.group("works")):
            entries.append(
                ParsedGradeEntry(
                    source_date=current_date,
                    group_label=group_label,
                    student_label=student_label,
                    grade=int(match.group("grade")),
                    work_number=work_number,
                    raw_line=raw_line.strip(),
                    line_number=line_number,
                )
            )
    return entries


def _parse_date(value: str) -> date:
    day, month, year = value.split(".")
    full_year = int(year) + 2000 if len(year) == 2 else int(year)
    return date(full_year, int(month), int(day))


def _clean_group(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().removeprefix("Группа").strip()
    if normalized.lower().startswith(("без указанной", "заметки")):
        return None
    return normalized or None


def _extract_student_and_group(prefix: str, current_group: str | None) -> tuple[str, str | None]:
    cleaned = re.sub(r"\([^)]*\)", "", prefix).replace("-", " ").strip(" ,")
    group_label = current_group
    inline_group = INLINE_GROUP_RE.search(cleaned)
    if inline_group:
        group_label = _clean_group(inline_group.group("group"))
        cleaned = (cleaned[: inline_group.start()] + " " + cleaned[inline_group.end() :]).strip()
    return re.sub(r"\s+", " ", cleaned), group_label


def _expand_work_numbers(value: str) -> list[int]:
    compact = value.replace(" ", "")
    if "-" not in compact:
        return [int(compact)]
    start, end = (int(part) for part in compact.split("-", 1))
    if end < start:
        start, end = end, start
    return list(range(start, end + 1))
