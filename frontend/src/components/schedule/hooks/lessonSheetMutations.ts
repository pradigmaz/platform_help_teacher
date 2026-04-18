'use client';

import type { AttendanceStatus, StudentGradeData } from '../types';
import { ATTENDANCE_CYCLE } from '../constants';

export const getNextAttendanceStatus = (
  current: AttendanceStatus | null | undefined
): AttendanceStatus | null => {
  if (!current) {
    return 'PRESENT';
  }

  if (current === ATTENDANCE_CYCLE[ATTENDANCE_CYCLE.length - 1]) {
    return null;
  }

  const idx = ATTENDANCE_CYCLE.indexOf(current);
  return idx >= 0 ? ATTENDANCE_CYCLE[idx + 1] : ATTENDANCE_CYCLE[0];
};

export const setAttendanceStatusState = (
  currentAttendance: Record<string, AttendanceStatus | null>,
  studentId: string,
  status: AttendanceStatus | null
) => {
  if (!status) {
    const nextAttendance = { ...currentAttendance };
    delete nextAttendance[studentId];
    return nextAttendance;
  }

  return { ...currentAttendance, [studentId]: status };
};

export const cycleAttendanceState = (
  currentAttendance: Record<string, AttendanceStatus | null>,
  studentId: string
) => setAttendanceStatusState(currentAttendance, studentId, getNextAttendanceStatus(currentAttendance[studentId] ?? null));

export const updateGradeState = (
  currentGrades: Record<string, StudentGradeData>,
  studentId: string,
  grade: number,
  defaultWorkNumber: number | null
) => {
  const currentGrade = currentGrades[studentId];
  if (currentGrade?.grade === grade) {
    const nextGrades = { ...currentGrades };
    delete nextGrades[studentId];
    return nextGrades;
  }

  return {
    ...currentGrades,
    [studentId]: {
      grade,
      work_number: currentGrade?.work_number ?? defaultWorkNumber,
    },
  };
};

export const updateStudentWorkNumberState = (
  currentGrades: Record<string, StudentGradeData>,
  studentId: string,
  nextWorkNumber: number
) => {
  const currentGrade = currentGrades[studentId];

  return {
    ...currentGrades,
    [studentId]: {
      grade: currentGrade?.grade ?? null,
      work_number: nextWorkNumber,
    },
  };
};

export const hasResolvedGradeWorkNumber = (
  selectedWorkNumber: number | null,
  defaultWorkNumber: number | null
) => selectedWorkNumber !== null || defaultWorkNumber !== null;

export const stripIncompleteGradeSelections = (
  currentGrades: Record<string, StudentGradeData>
) =>
  Object.fromEntries(
    Object.entries(currentGrades).filter(([, gradeData]) => {
      if (gradeData.has_conflict || (gradeData.grade_items?.length ?? 0) > 1) {
        return true;
      }
      return gradeData.grade === null || gradeData.work_number !== null;
    })
  ) as Record<string, StudentGradeData>;
