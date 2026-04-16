'use client';

import type { StudentGradeData } from '../types';
import type {
  RestoredLectureDraft,
  RestoredLessonDraft,
  RestoredSheetDraft,
} from './sheetDraftTypes';

const SHEET_DRAFT_KEY = 'platforma_maga:sheet-draft:v1';
const SHEET_RECOVERY_KEY = 'platforma_maga:sheet-draft-recovery:v1';
const DRAFT_TTL_MS = 12 * 60 * 60 * 1000;

function isStorageAvailable(): boolean {
  return typeof window !== 'undefined' && typeof window.sessionStorage !== 'undefined';
}

function readStoredDraft(): RestoredSheetDraft | null {
  if (!isStorageAvailable()) {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(SHEET_DRAFT_KEY);
    if (!raw) {
      return null;
    }

    const draft = JSON.parse(raw) as RestoredSheetDraft;
    const savedAt = Date.parse(draft.savedAt);
    if (!Number.isFinite(savedAt) || Date.now() - savedAt > DRAFT_TTL_MS) {
      clearSheetDraft();
      return null;
    }

    return draft;
  } catch {
    clearSheetDraft();
    return null;
  }
}

function writeStoredDraft(draft: RestoredSheetDraft): void {
  if (!isStorageAvailable()) {
    return;
  }

  window.sessionStorage.setItem(SHEET_DRAFT_KEY, JSON.stringify(draft));
}

function cloneGrades(grades: Record<string, StudentGradeData>): Record<string, StudentGradeData> {
  return Object.fromEntries(
    Object.entries(grades).map(([studentId, gradeData]) => [studentId, { ...gradeData }])
  );
}

export function readSheetDraft(): RestoredSheetDraft | null {
  return readStoredDraft();
}

export function saveLessonSheetDraft(draft: Omit<RestoredLessonDraft, 'savedAt'>): void {
  writeStoredDraft({
    ...draft,
    attendance: { ...draft.attendance },
    grades: cloneGrades(draft.grades),
    savedAt: new Date().toISOString(),
  });
}

export function saveLectureSheetDraft(draft: Omit<RestoredLectureDraft, 'savedAt'>): void {
  writeStoredDraft({
    ...draft,
    attendanceByGroup: Object.fromEntries(
      Object.entries(draft.attendanceByGroup).map(([groupId, attendance]) => [
        groupId,
        { ...attendance },
      ])
    ),
    savedAt: new Date().toISOString(),
  });
}

export function clearSheetDraft(): void {
  if (!isStorageAvailable()) {
    return;
  }

  window.sessionStorage.removeItem(SHEET_DRAFT_KEY);
  window.sessionStorage.removeItem(SHEET_RECOVERY_KEY);
}

export function markSheetRecoveryPending(): void {
  if (!isStorageAvailable()) {
    return;
  }

  window.sessionStorage.setItem(SHEET_RECOVERY_KEY, '1');
}

export function consumeSheetRecoveryPending(): boolean {
  if (!isStorageAvailable()) {
    return false;
  }

  const isPending = window.sessionStorage.getItem(SHEET_RECOVERY_KEY) === '1';
  if (isPending) {
    window.sessionStorage.removeItem(SHEET_RECOVERY_KEY);
  }
  return isPending;
}
