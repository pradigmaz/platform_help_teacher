'use client';

import type { AttendanceStatus, StudentGradeData } from '../types';
import { ATTENDANCE_CYCLE } from '../constants';

export const cycleAttendanceState = (
  currentAttendance: Record<string, AttendanceStatus | null>,
  studentId: string
) => {
  const current = currentAttendance[studentId] ?? null;
  if (!current) {
    return { ...currentAttendance, [studentId]: 'PRESENT' as const };
  }

  if (current === ATTENDANCE_CYCLE[ATTENDANCE_CYCLE.length - 1]) {
    const nextAttendance = { ...currentAttendance };
    delete nextAttendance[studentId];
    return nextAttendance;
  }

  const idx = ATTENDANCE_CYCLE.indexOf(current);
  const next = idx >= 0 ? ATTENDANCE_CYCLE[idx + 1] : ATTENDANCE_CYCLE[0];
  return { ...currentAttendance, [studentId]: next };
};

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
