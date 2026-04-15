'use client';
import type { AttendanceStatus, LessonData, LessonStatus, StudentGradeData } from '../types';

export type SavedLessonState = Pick<LessonData, 'id' | 'topic' | 'work_number' | 'is_cancelled' | 'ended_early'>;
export type LessonSnapshot = Pick<
  LessonData,
  | 'id'
  | 'group_id'
  | 'subgroup'
  | 'subject_id'
  | 'topic'
  | 'work_number'
  | 'is_cancelled'
  | 'ended_early'
>;

export type SheetAttendanceUpdate = {
  student_id: string;
  status: AttendanceStatus | null;
};

export type SheetGradeUpdate = {
  student_id: string;
  grade: number | null;
  work_number?: number | null;
  has_conflict?: boolean;
  conflict_count?: number;
  grade_items?: Array<{
    grade: number;
    work_number: number | null;
  }>;
};

type SheetResponse = {
  lesson?: Partial<SavedLessonState> & {
    status?: LessonStatus;
    lesson_work_number?: number | null;
  };
  topic?: string | null;
  work_number?: number | null;
  lesson_work_number?: number | null;
  status?: LessonStatus;
  is_cancelled?: boolean;
  ended_early?: boolean;
  attendance?: SheetAttendanceUpdate[];
  attendance_updates?: SheetAttendanceUpdate[];
  grades?: SheetGradeUpdate[];
  grade_updates?: SheetGradeUpdate[];
};

export const cloneGradeMap = (gradeMap: Record<string, StudentGradeData>) =>
  Object.fromEntries(
    Object.entries(gradeMap).map(([studentId, gradeData]) => [studentId, { ...gradeData }])
  ) as Record<string, StudentGradeData>;

const buildAttendanceMap = (updates: SheetAttendanceUpdate[]) => {
  const nextAttendance: Record<string, AttendanceStatus | null> = {};
  for (const update of updates) {
    if (update.status) {
      nextAttendance[update.student_id] = update.status;
    }
  }
  return nextAttendance;
};

const normalizeGrade = (update: SheetGradeUpdate): StudentGradeData | null => {
  if (update.has_conflict) {
    return {
      grade: null,
      work_number: null,
      has_conflict: true,
      conflict_count: update.conflict_count ?? 2,
      grade_items: update.grade_items ?? [],
    };
  }

  if (update.grade === null) {
    return null;
  }

  return {
    grade: update.grade,
    work_number: update.work_number ?? null,
    has_conflict: false,
    conflict_count: 0,
    grade_items: update.grade_items ?? [
      {
        grade: update.grade,
        work_number: update.work_number ?? null,
      },
    ],
  };
};

export const buildGradeMap = (updates: SheetGradeUpdate[]) => {
  const nextGrades: Record<string, StudentGradeData> = {};
  for (const update of updates) {
    const gradeData = normalizeGrade(update);
    if (gradeData) {
      nextGrades[update.student_id] = gradeData;
    }
  }
  return nextGrades;
};

export const applyAttendanceUpdates = (
  currentAttendance: Record<string, AttendanceStatus | null>,
  updates: SheetAttendanceUpdate[]
) => {
  const nextAttendance = { ...currentAttendance };
  for (const update of updates) {
    if (update.status) {
      nextAttendance[update.student_id] = update.status;
    } else {
      delete nextAttendance[update.student_id];
    }
  }
  return nextAttendance;
};

export const applyGradeUpdates = (
  currentGrades: Record<string, StudentGradeData>,
  updates: SheetGradeUpdate[]
) => {
  const nextGrades = cloneGradeMap(currentGrades);
  for (const update of updates) {
    const gradeData = normalizeGrade(update);
    if (gradeData) {
      nextGrades[update.student_id] = gradeData;
    } else {
      delete nextGrades[update.student_id];
    }
  }
  return nextGrades;
};

const toComparableGrade = (gradeData?: StudentGradeData) => {
  if (!gradeData || gradeData.grade === null) {
    return null;
  }

  return {
    grade: gradeData.grade,
    work_number: gradeData.work_number ?? null,
    grade_items: gradeData.grade_items ?? [],
  };
};

export const isSameGrade = (left?: StudentGradeData, right?: StudentGradeData) => {
  const leftGrade = toComparableGrade(left);
  const rightGrade = toComparableGrade(right);

  return (
    leftGrade?.grade === rightGrade?.grade &&
    leftGrade?.work_number === rightGrade?.work_number &&
    JSON.stringify(leftGrade?.grade_items ?? []) === JSON.stringify(rightGrade?.grade_items ?? [])
  );
};

export const buildAttendanceUpdates = (
  initialAttendance: Record<string, AttendanceStatus | null>,
  currentAttendance: Record<string, AttendanceStatus | null>
): SheetAttendanceUpdate[] => {
  const studentIds = new Set([
    ...Object.keys(initialAttendance),
    ...Object.keys(currentAttendance),
  ]);

  return Array.from(studentIds)
    .map((studentId) => ({
      student_id: studentId,
      status: currentAttendance[studentId] ?? null,
    }))
    .filter(
      ({ student_id, status }) => (initialAttendance[student_id] ?? null) !== status
    );
};

export const buildGradeUpdates = (
  initialGrades: Record<string, StudentGradeData>,
  currentGrades: Record<string, StudentGradeData>
): SheetGradeUpdate[] => {
  const studentIds = new Set([
    ...Object.keys(initialGrades),
    ...Object.keys(currentGrades),
  ]);

  return Array.from(studentIds).reduce<SheetGradeUpdate[]>((updates, studentId) => {
    const initialGrade = initialGrades[studentId];
    const currentGrade = currentGrades[studentId];
    const hasReadOnlyMultiGrade =
      (!initialGrade?.has_conflict && (initialGrade?.grade_items?.length ?? 0) > 1) ||
      (!currentGrade?.has_conflict && (currentGrade?.grade_items?.length ?? 0) > 1);
    if (hasReadOnlyMultiGrade) {
      return updates;
    }

    const nextUpdate =
      !currentGrade || currentGrade.grade === null
        ? { student_id: studentId, grade: null, work_number: null }
        : {
            student_id: studentId,
            grade: currentGrade.grade,
            work_number: currentGrade.work_number ?? null,
          };
    if (
      !isSameGrade(
        initialGrades[studentId],
        nextUpdate.grade === null
          ? undefined
          : { grade: nextUpdate.grade, work_number: nextUpdate.work_number ?? null }
      )
    ) {
      updates.push(nextUpdate);
    }
    return updates;
  }, []);
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === 'object';

export const getLessonStatus = (
  lessonState: Pick<SavedLessonState, 'is_cancelled' | 'ended_early'>
) => (lessonState.is_cancelled ? 'cancelled' : lessonState.ended_early ? 'early' : 'normal');

export const extractServerState = (
  responseData: unknown,
  fallbackState: {
    lesson: SavedLessonState;
    attendance: Record<string, AttendanceStatus | null>;
    grades: Record<string, StudentGradeData>;
  }
) => {
  if (!isRecord(responseData)) {
    return null;
  }

  const payload = responseData as SheetResponse;
  const lessonSource = isRecord(payload.lesson) ? payload.lesson : payload;
  const hasLessonState =
    isRecord(payload.lesson) ||
    ['topic', 'lesson_work_number', 'work_number', 'status', 'is_cancelled', 'ended_early'].some(
      (key) => key in payload
    );
  const fullAttendance = Array.isArray(payload.attendance) ? payload.attendance : null;
  const attendanceUpdates = Array.isArray(payload.attendance_updates)
    ? payload.attendance_updates
    : null;
  const fullGrades = Array.isArray(payload.grades) ? payload.grades : null;
  const gradeUpdates = Array.isArray(payload.grade_updates) ? payload.grade_updates : null;

  if (!hasLessonState && !fullAttendance && !attendanceUpdates && !fullGrades && !gradeUpdates) {
    return null;
  }

  const nextLesson: SavedLessonState = { ...fallbackState.lesson };
  const responseStatus =
    lessonSource.status === 'normal' ||
    lessonSource.status === 'cancelled' ||
    lessonSource.status === 'early'
      ? lessonSource.status
      : null;

  if (typeof lessonSource.topic === 'string' || lessonSource.topic === null) {
    nextLesson.topic = lessonSource.topic;
  }
  if (
    typeof lessonSource.lesson_work_number === 'number' ||
    lessonSource.lesson_work_number === null
  ) {
    nextLesson.work_number = lessonSource.lesson_work_number;
  } else if (typeof lessonSource.work_number === 'number' || lessonSource.work_number === null) {
    nextLesson.work_number = lessonSource.work_number;
  }
  if (typeof lessonSource.is_cancelled === 'boolean') {
    nextLesson.is_cancelled = lessonSource.is_cancelled;
  } else if (responseStatus) {
    nextLesson.is_cancelled = responseStatus === 'cancelled';
  }
  if (typeof lessonSource.ended_early === 'boolean') {
    nextLesson.ended_early = lessonSource.ended_early;
  } else if (responseStatus) {
    nextLesson.ended_early = responseStatus === 'early';
  }

  return {
    lesson: nextLesson,
    attendance: fullAttendance
      ? buildAttendanceMap(fullAttendance)
      : attendanceUpdates
        ? applyAttendanceUpdates(fallbackState.attendance, attendanceUpdates)
        : fallbackState.attendance,
    grades: fullGrades
      ? buildGradeMap(fullGrades)
      : gradeUpdates
        ? applyGradeUpdates(fallbackState.grades, gradeUpdates)
        : fallbackState.grades,
  };
};
