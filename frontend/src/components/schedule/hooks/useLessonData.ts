'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import type { AxiosError } from 'axios';
import { toast } from 'sonner';
import api, { ApiError } from '@/lib/api';
import type { Student, LessonData, LessonStatus, AttendanceStatus, StudentGradeData, LessonSheetSyncData } from '../types';
import { canHaveGrade } from '../constants';
import {
  hasResolvedGradeWorkNumber,
  stripIncompleteGradeSelections,
  updateGradeState,
  updateStudentWorkNumberState,
  setAttendanceStatusState,
} from './lessonSheetMutations';
import {
  buildAttendanceUpdates,
  buildGradeUpdates,
  cloneGradeMap,
  extractServerState,
  getLessonStatus,
  type LessonSnapshot,
  type SavedLessonState,
} from './lessonSheetState';
import { loadLessonSheetResources } from './lessonSheetQueries';
import { isFutureLessonDate } from './lessonDateGuards';
import { clearSheetDraft, saveLessonSheetDraft } from './sheetDraftStorage';
import type { RestoredLessonDraft, SheetDraftContext } from './sheetDraftTypes';

interface UseLessonDataProps {
  lesson: LessonData | null;
  isOpen: boolean;
  draftContext: SheetDraftContext;
  restoredDraft?: RestoredLessonDraft | null;
}

interface UseLessonDataReturn {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  grades: Record<string, StudentGradeData>;
  availableWorkNumbers: number[];
  topic: string;
  workNumber: number | null;
  status: LessonStatus;
  isLoading: boolean;
  hasChanges: boolean;
  setTopic: (topic: string) => void;
  setWorkNumber: (workNumber: number | null) => void;
  setStatus: (status: LessonStatus) => void;
  setAttendanceStatus: (studentId: string, status: AttendanceStatus | null) => void;
  setGrade: (studentId: string, grade: number, workNumber: number | null) => void;
  setStudentWorkNumber: (studentId: string, workNumber: number) => void;
  saveAll: () => Promise<LessonSheetSyncData | null>;
  resetChanges: () => void;
}

export function useLessonData({
  lesson,
  isOpen,
  draftContext,
  restoredDraft = null,
}: UseLessonDataProps): UseLessonDataReturn {
  const [students, setStudents] = useState<Student[]>([]);
  const [attendance, setAttendance] = useState<Record<string, AttendanceStatus | null>>({});
  const [grades, setGrades] = useState<Record<string, StudentGradeData>>({});
  const [availableWorkNumbers, setAvailableWorkNumbers] = useState<number[]>([]);
  const [topic, setTopicState] = useState('');
  const [workNumber, setWorkNumberState] = useState<number | null>(null);
  const [status, setStatusState] = useState<LessonStatus>('normal');
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const initialAttendanceRef = useRef<Record<string, AttendanceStatus | null>>({});
  const initialGradesRef = useRef<Record<string, StudentGradeData>>({});
  const initialLessonRef = useRef<SavedLessonState | null>(null);
  const lessonSnapshot = useMemo<LessonSnapshot | null>(() => {
    if (!lesson) {
      return null;
    }
    return {
      id: lesson.id,
      group_id: lesson.group_id,
      subgroup: lesson.subgroup,
      subject_id: lesson.subject_id,
      topic: lesson.topic,
      work_number: lesson.work_number,
      is_cancelled: lesson.is_cancelled,
      ended_early: lesson.ended_early,
    };
  }, [lesson]);

  const loadData = useCallback(async (currentLesson: LessonSnapshot) => {
    setIsLoading(true);
    const initialLesson: SavedLessonState = {
      id: currentLesson.id,
      topic: currentLesson.topic ?? null,
      work_number: currentLesson.work_number ?? null,
      is_cancelled: currentLesson.is_cancelled,
      ended_early: currentLesson.ended_early ?? false,
    };
    initialLessonRef.current = initialLesson;
    initialAttendanceRef.current = {};
    initialGradesRef.current = {};
    setStudents([]);
    setAttendance({});
    setGrades({});
    setAvailableWorkNumbers([]);
    setTopicState(initialLesson.topic || '');
    setWorkNumberState(initialLesson.work_number ?? null);
    setStatusState(getLessonStatus(initialLesson));
    setHasChanges(false);

    try {
      const nextResources = await loadLessonSheetResources(currentLesson);
      setStudents(nextResources.students);
      setAttendance(nextResources.attendance);
      setGrades(nextResources.grades);
      setAvailableWorkNumbers(nextResources.availableWorkNumbers);
      initialAttendanceRef.current = { ...nextResources.attendance };
      initialGradesRef.current = cloneGradeMap(nextResources.grades);

      if (restoredDraft?.lessonId === currentLesson.id) {
        const restoredGrades = stripIncompleteGradeSelections(cloneGradeMap(restoredDraft.grades));
        setTopicState(restoredDraft.topic);
        setWorkNumberState(restoredDraft.workNumber);
        setStatusState(restoredDraft.status);
        setAttendance({ ...restoredDraft.attendance });
        setGrades(restoredGrades);
        setHasChanges(true);
      }
    } catch (err) {
      console.error('Ошибка загрузки данных занятия', err);
    } finally {
      setIsLoading(false);
    }
  }, [restoredDraft]);

  useEffect(() => {
    if (lessonSnapshot && isOpen) {
      loadData(lessonSnapshot);
    }
  }, [lessonSnapshot, isOpen, loadData]);

  const setTopic = (value: string) => { setTopicState(value); setHasChanges(true); };
  const setWorkNumber = (value: number | null) => { setWorkNumberState(value); setHasChanges(true); };
  const setStatus = (value: LessonStatus) => { setStatusState(value); setHasChanges(true); };

  const setAttendanceStatus = (studentId: string, nextStatus: AttendanceStatus | null) => {
    setAttendance((prev) => setAttendanceStatusState(prev, studentId, nextStatus));
    setHasChanges(true);
  };

  const setGrade = (studentId: string, grade: number, selectedWorkNumber: number | null) => {
    if (grades[studentId]?.has_conflict) {
      toast.error('Сначала разберите конфликт оценок в журнале');
      return;
    }

    const defaultWorkNumber =
      workNumber !== null && availableWorkNumbers.includes(workNumber) ? workNumber : null;
    if (!hasResolvedGradeWorkNumber(selectedWorkNumber, defaultWorkNumber)) {
      toast.error('Сначала укажите номер лабораторной');
      return;
    }
    setGrades((prev) =>
      updateGradeState(prev, studentId, grade, selectedWorkNumber ?? defaultWorkNumber)
    );
    setHasChanges(true);
  };

  const setStudentWorkNumber = (studentId: string, nextWorkNumber: number) => {
    if (grades[studentId]?.has_conflict) {
      toast.error('Сначала разберите конфликт оценок в журнале');
      return;
    }

    setGrades((prev) => updateStudentWorkNumberState(prev, studentId, nextWorkNumber));
    setHasChanges(true);
  };

  const saveAll = async () => {
    if (!lesson) return null;
    setIsLoading(true);

    try {
      const attendanceUpdates = buildAttendanceUpdates(initialAttendanceRef.current, attendance);
      const gradeUpdates = buildGradeUpdates(initialGradesRef.current, grades);

      if (
        canHaveGrade(lesson.lesson_type) &&
        gradeUpdates.some(({ grade, work_number }) => grade !== null && work_number == null)
      ) {
        toast.error('Для оценки нужно указать номер лабораторной');
        throw new Error('work_number_required');
      }
      if (isFutureLessonDate(lesson.date) && attendanceUpdates.length > 0) {
        toast.error('Посещаемость можно отмечать только в день занятия или позже');
        throw new Error('future_attendance_blocked');
      }

      saveLessonSheetDraft({
        kind: 'lesson',
        context: draftContext,
        lessonId: lesson.id,
        topic,
        workNumber,
        status,
        attendance,
        grades,
      });

      const { data } = await api.post(`/admin/lessons/${lesson.id}/sheet`, {
        topic,
        lesson_work_number: workNumber,
        status,
        attendance_updates: attendanceUpdates,
        grade_updates: gradeUpdates,
      });

      const fallbackState = {
        lesson: {
          id: lesson.id,
          topic: topic || null,
          work_number: workNumber,
          is_cancelled: status === 'cancelled',
          ended_early: status === 'early',
        },
        attendance: { ...attendance },
        grades: cloneGradeMap(grades),
      };
      const nextState = extractServerState(data, fallbackState) ?? fallbackState;

      initialLessonRef.current = nextState.lesson;
      initialAttendanceRef.current = { ...nextState.attendance };
      initialGradesRef.current = cloneGradeMap(nextState.grades);

      setAttendance(nextState.attendance);
      setGrades(nextState.grades);
      setTopicState(nextState.lesson.topic || '');
      setWorkNumberState(nextState.lesson.work_number ?? null);
      setStatusState(getLessonStatus(nextState.lesson));
      setHasChanges(false);
      clearSheetDraft();
      return {
        lesson: nextState.lesson,
        attendance: { ...nextState.attendance },
        grades: cloneGradeMap(nextState.grades),
      };
    } catch (err) {
      const localValidationError =
        (err as Error).message === 'work_number_required' ||
        (err as Error).message === 'future_attendance_blocked';
      const handledApiError = err instanceof ApiError && !err.isRetryable;
      if (!localValidationError && !handledApiError) {
        console.error('Ошибка сохранения', err);
      }
      if (localValidationError) {
        throw err;
      }
      const detail =
        (err instanceof ApiError ? err.message : undefined) ||
        ((err as AxiosError<{ detail?: string }>).response?.data?.detail as string | undefined) ||
        'Ошибка сохранения';
      toast.error(detail);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const resetChanges = () => {
    if (initialLessonRef.current) {
      setTopicState(initialLessonRef.current.topic || '');
      setWorkNumberState(initialLessonRef.current.work_number ?? null);
      setStatusState(getLessonStatus(initialLessonRef.current));
    }
    setAttendance({ ...initialAttendanceRef.current });
    setGrades(cloneGradeMap(initialGradesRef.current));
    setHasChanges(false);
  };

  return {
    students,
    attendance,
    grades,
    availableWorkNumbers,
    topic,
    workNumber,
    status,
    isLoading,
    hasChanges,
    setTopic,
    setWorkNumber,
    setStatus,
    setAttendanceStatus,
    setGrade,
    setStudentWorkNumber,
    saveAll,
    resetChanges,
  };
}
