import type { AttestationResult } from '@/lib/api';
import type { GradeData, Lesson, Student } from '../lib/journal-constants';

export function sortJournalLessons(lessons: Lesson[]): Lesson[] {
  return [...lessons].sort((left, right) => {
    const dateCompare = left.date.localeCompare(right.date);
    if (dateCompare !== 0) {
      return dateCompare;
    }
    return left.lesson_number - right.lesson_number;
  });
}

export function buildMaxWorkNumberMap(lessons: Lesson[]): Record<string, number> {
  return lessons.reduce<Record<string, number>>((accumulator, lesson) => {
    const key = lesson.lesson_type.toLowerCase();
    const current = accumulator[key] ?? 0;
    accumulator[key] = Math.max(current, lesson.work_number ?? 0);
    return accumulator;
  }, {});
}

function areGradeDataEqual(left: GradeData | undefined, right: GradeData | undefined): boolean {
  if (left === right) {
    return true;
  }

  return (
    left?.grade === right?.grade &&
    left?.work_number === right?.work_number &&
    left?.has_conflict === right?.has_conflict &&
    left?.conflict_count === right?.conflict_count &&
    JSON.stringify(left?.grade_items ?? []) === JSON.stringify(right?.grade_items ?? [])
  );
}

export function calculateAttendancePercentage(
  lessons: Lesson[],
  attendance: Record<string, Record<string, string>>,
  studentId: string
): number | null {
  let present = 0;
  let total = 0;

  for (const lesson of lessons) {
    const status = attendance[lesson.id]?.[studentId];
    if (!status) {
      continue;
    }

    total += 1;
    if (status === 'PRESENT' || status === 'LATE') {
      present += 1;
    }
  }

  return total > 0 ? Math.round((present / total) * 100) : null;
}

export function isLessonDisabledForStudent(lesson: Lesson, student: Student): boolean {
  return (
    lesson.subgroup !== null &&
    student.subgroup !== null &&
    lesson.subgroup !== student.subgroup
  );
}

export function getAttestationGradeColor(grade: string): string {
  switch (grade) {
    case 'отл':
      return 'text-green-600 bg-green-50 dark:bg-green-950/30';
    case 'хор':
      return 'text-blue-600 bg-blue-50 dark:bg-blue-950/30';
    case 'уд':
      return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950/30';
    case 'неуд':
      return 'text-red-600 bg-red-50 dark:bg-red-950/30';
    default:
      return 'text-muted-foreground';
  }
}

export interface JournalStudentRowModel {
  percentage: number | null;
  attestation: AttestationResult | null;
  gradesByLesson: Record<string, GradeData | undefined>;
  attendanceByLesson: Record<string, string | undefined>;
}

export function buildJournalStudentRowModel(
  lessons: Lesson[],
  attendance: Record<string, Record<string, string>>,
  grades: Record<string, Record<string, GradeData>>,
  attestationScores: Record<string, AttestationResult> | undefined,
  studentId: string
): JournalStudentRowModel {
  return {
    percentage: calculateAttendancePercentage(lessons, attendance, studentId),
    attestation: attestationScores?.[studentId] ?? null,
    gradesByLesson: Object.fromEntries(lessons.map((lesson) => [lesson.id, grades[lesson.id]?.[studentId]])),
    attendanceByLesson: Object.fromEntries(lessons.map((lesson) => [lesson.id, attendance[lesson.id]?.[studentId]])),
  };
}

export function isJournalStudentLessonStateEqual(
  lessons: Lesson[],
  studentId: string,
  previousAttendance: Record<string, Record<string, string>>,
  nextAttendance: Record<string, Record<string, string>>,
  previousGrades: Record<string, Record<string, GradeData>>,
  nextGrades: Record<string, Record<string, GradeData>>,
): boolean {
  for (const lesson of lessons) {
    if (previousAttendance[lesson.id]?.[studentId] !== nextAttendance[lesson.id]?.[studentId]) {
      return false;
    }

    if (!areGradeDataEqual(previousGrades[lesson.id]?.[studentId], nextGrades[lesson.id]?.[studentId])) {
      return false;
    }
  }

  return true;
}
