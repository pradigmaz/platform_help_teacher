'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import {
  clearSheetDraft,
  consumeSheetRecoveryPending,
  readSheetDraft,
} from '@/components/schedule/hooks/sheetDraftStorage';
import type { JournalDraftContext, RestoredLessonDraft } from '@/components/schedule/hooks/sheetDraftTypes';
import type { Lesson } from '../lib/journal-constants';
import type { AttestationPeriod, SemesterInfo } from './useJournalData';

type RestoredJournalLessonDraft = RestoredLessonDraft & { context: JournalDraftContext };

function getInitialRecoveredDraft(): RestoredJournalLessonDraft | null {
  if (!consumeSheetRecoveryPending()) return null;
  const draft = readSheetDraft();
  return draft?.kind === 'lesson' && draft.context.route === 'journal'
    ? (draft as RestoredJournalLessonDraft)
    : null;
}

interface UseJournalSheetRecoveryProps {
  lessons: Lesson[];
  isLoading: boolean;
  selectedGroupId: string;
  setSelectedGroupId: (groupId: string) => void;
  selectedSubjectId: string;
  setSelectedSubjectId: (subjectId: string) => void;
  selectedLessonType: string;
  setSelectedLessonType: (lessonType: string) => void;
  currentWeek: Date;
  setCurrentWeek: (date: Date) => void;
  attestationPeriod: AttestationPeriod;
  setAttestationPeriod: (period: AttestationPeriod) => void;
  selectedSemester: SemesterInfo;
  setSelectedSemester: (semester: SemesterInfo) => void;
  setSelectedLesson: (lesson: Lesson | null) => void;
}

function parseDateOnly(value: string): Date {
  return new Date(`${value}T00:00:00`);
}

export function useJournalSheetRecovery({
  lessons,
  isLoading,
  selectedGroupId,
  setSelectedGroupId,
  selectedSubjectId,
  setSelectedSubjectId,
  selectedLessonType,
  setSelectedLessonType,
  currentWeek,
  setCurrentWeek,
  attestationPeriod,
  setAttestationPeriod,
  selectedSemester,
  setSelectedSemester,
  setSelectedLesson,
}: UseJournalSheetRecoveryProps) {
  const [restoredDraft, setRestoredDraft] = useState<RestoredJournalLessonDraft | null>(
    getInitialRecoveredDraft
  );
  const recoveryHandledRef = useRef(restoredDraft === null);

  const clearRestoredDraft = useCallback(() => {
    clearSheetDraft();
    setRestoredDraft(null);
    recoveryHandledRef.current = true;
  }, []);

  useEffect(() => {
    if (!restoredDraft || recoveryHandledRef.current) {
      return;
    }

    const { context } = restoredDraft;
    let synced = false;

    if (selectedGroupId !== context.groupId) {
      setSelectedGroupId(context.groupId);
      synced = true;
    }
    if (selectedSubjectId !== context.subjectId) {
      setSelectedSubjectId(context.subjectId);
      synced = true;
    }
    if (selectedLessonType !== context.lessonType) {
      setSelectedLessonType(context.lessonType);
      synced = true;
    }
    if (attestationPeriod !== context.attestationPeriod) {
      setAttestationPeriod(context.attestationPeriod);
      synced = true;
    }
    if (
      selectedSemester.academicYear !== context.semester.academicYear ||
      selectedSemester.semester !== context.semester.semester
    ) {
      setSelectedSemester(context.semester);
      synced = true;
    }
    if (format(currentWeek, 'yyyy-MM-dd') !== context.weekStartIso) {
      setCurrentWeek(parseDateOnly(context.weekStartIso));
      synced = true;
    }

    if (synced || isLoading) {
      return;
    }

    const lesson = lessons.find((item) => item.id === restoredDraft.lessonId);
    if (lesson) {
      recoveryHandledRef.current = true;
      setSelectedLesson(lesson);
      toast.warning('Сессия истекла во время сохранения. Черновик восстановлен, сохраните ещё раз.');
      return;
    }

    toast.error('Черновик найден, но нужное занятие в журнале больше не найдено.');
    queueMicrotask(clearRestoredDraft);
  }, [
    attestationPeriod,
    clearRestoredDraft,
    currentWeek,
    isLoading,
    lessons,
    restoredDraft,
    recoveryHandledRef,
    selectedGroupId,
    selectedLessonType,
    selectedSemester,
    selectedSubjectId,
    setAttestationPeriod,
    setCurrentWeek,
    setSelectedGroupId,
    setSelectedLesson,
    setSelectedLessonType,
    setSelectedSemester,
    setSelectedSubjectId,
  ]);

  return { restoredDraft, clearRestoredDraft };
}
