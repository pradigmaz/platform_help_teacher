'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import type { AxiosError } from 'axios';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { Student, LessonData, LessonStatus, AttendanceStatus, StudentGradeData, LessonSheetSyncData } from '../types';
import { canHaveGrade } from '../constants';
import {
  cycleAttendanceState,
  updateGradeState,
  updateStudentWorkNumberState,
} from './lessonSheetMutations';
import {
  buildAttendanceUpdates,
  buildGradeMap,
  buildGradeUpdates,
  cloneGradeMap,
  extractServerState,
  getLessonStatus,
  type LessonSnapshot,
  type SavedLessonState,
} from './lessonSheetState';

interface UseLessonDataProps {
  lesson: LessonData | null;
  isOpen: boolean;
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
  cycleAttendance: (studentId: string) => void;
  setGrade: (studentId: string, grade: number, workNumber: number | null) => void;
  setStudentWorkNumber: (studentId: string, workNumber: number) => void;
  saveAll: () => Promise<LessonSheetSyncData | null>;
  resetChanges: () => void;
}

export function useLessonData({ lesson, isOpen }: UseLessonDataProps): UseLessonDataReturn {
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
      if (currentLesson.group_id) {
        try {
          const { data: groupData } = await api.get(`/groups/${currentLesson.group_id}`);
          let studentsList = groupData.students || [];
          
          if (currentLesson.subgroup !== null && currentLesson.subgroup !== undefined) {
            studentsList = studentsList.filter(
              (s: Student) => s.subgroup === currentLesson.subgroup
            );
          }
          setStudents(studentsList);
        } catch {
          console.warn('Could not load group');
          setStudents([]);
        }
      } else {
        setStudents([]);
      }

      if (currentLesson.group_id) {
        try {
          const { data: attData } = await api.get('/admin/journal/attendance', {
            params: { group_id: currentLesson.group_id, lesson_ids: [currentLesson.id] }
          });
          const attMap: Record<string, AttendanceStatus | null> = {};
          for (const a of attData) {
            attMap[a.student_id] = a.status as AttendanceStatus;
          }
          setAttendance(attMap);
          initialAttendanceRef.current = { ...attMap };
        } catch {
          setAttendance({});
          initialAttendanceRef.current = {};
        }
      } else {
        setAttendance({});
        initialAttendanceRef.current = {};
      }

      try {
        const { data: gradeData } = await api.get('/admin/journal/grades', {
          params: { lesson_ids: [currentLesson.id] }
        });
        const gradeMap = buildGradeMap(gradeData);
        setGrades(gradeMap);
        initialGradesRef.current = cloneGradeMap(gradeMap);
      } catch {
        setGrades({});
        initialGradesRef.current = {};
      }

      if (currentLesson.subject_id) {
        try {
          const { data: labs } = await api.get<Array<{ number: number }>>('/admin/labs', {
            params: {
              subject_id: currentLesson.subject_id,
              limit: 500,
            },
          });
          const workNumbers = Array.from(
            new Set(
              labs
                .map((lab) => lab.number)
                .filter((number): number is number => Number.isInteger(number) && number > 0)
            )
          ).sort((left, right) => left - right);
          setAvailableWorkNumbers(workNumbers);
        } catch {
          setAvailableWorkNumbers([]);
        }
      } else {
        setAvailableWorkNumbers([]);
      }
    } catch (err) {
      console.error('Ошибка загрузки данных занятия', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (lessonSnapshot && isOpen) {
      loadData(lessonSnapshot);
    }
  }, [lessonSnapshot, isOpen, loadData]);

  const setTopic = (value: string) => {
    setTopicState(value);
    setHasChanges(true);
  };
  const setWorkNumber = (value: number | null) => {
    setWorkNumberState(value);
    setHasChanges(true);
  };
  const setStatus = (value: LessonStatus) => {
    setStatusState(value);
    setHasChanges(true);
  };

  const cycleAttendance = (studentId: string) => {
    setAttendance((prev) => cycleAttendanceState(prev, studentId));
    setHasChanges(true);
  };

  const setGrade = (studentId: string, grade: number, selectedWorkNumber: number | null) => {
    if (grades[studentId]?.has_conflict) {
      toast.error('Сначала разберите конфликт оценок в журнале');
      return;
    }

    const defaultWorkNumber =
      workNumber !== null && availableWorkNumbers.includes(workNumber) ? workNumber : null;
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
      return {
        lesson: nextState.lesson,
        attendance: { ...nextState.attendance },
        grades: cloneGradeMap(nextState.grades),
      };
    } catch (err) {
      console.error('Ошибка сохранения', err);
      if ((err as Error).message === 'work_number_required') {
        throw err;
      }
      const detail =
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
    cycleAttendance,
    setGrade,
    setStudentWorkNumber,
    saveAll,
    resetChanges,
  };
}
