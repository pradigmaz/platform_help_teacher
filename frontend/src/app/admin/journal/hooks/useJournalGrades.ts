'use client';

import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import api, { AttestationAPI, AttestationType, AttestationResult } from '@/lib/api';
import type { GradeData } from '../lib/journal-constants';
import type { AttestationPeriod } from './useJournalFilters';

export interface UseJournalGradesReturn {
  grades: Record<string, Record<string, GradeData>>;
  setGrades: React.Dispatch<React.SetStateAction<Record<string, Record<string, GradeData>>>>;
  attestationScores: Record<string, AttestationResult>;
  setAttestationScores: React.Dispatch<React.SetStateAction<Record<string, AttestationResult>>>;
  updateGrade: (lessonId: string, studentId: string, grade: number | null, workNumber?: number | null) => Promise<void>;
  loadGrades: (lessonIds: string[]) => Promise<void>;
  loadAttestationScores: (groupId: string, period: AttestationPeriod, subjectId?: string) => Promise<void>;
  isSaving: boolean;
}

interface UseJournalGradesProps {
  onStatsRefetch: () => void;
}

const STATS_DEBOUNCE_MS = 300;

export function useJournalGrades({ onStatsRefetch }: UseJournalGradesProps): UseJournalGradesReturn {
  const [grades, setGrades] = useState<Record<string, Record<string, GradeData>>>({});
  const [attestationScores, setAttestationScores] = useState<Record<string, AttestationResult>>({});
  const [isSaving, setIsSaving] = useState(false);
  const statsDebounceRef = useRef<NodeJS.Timeout | null>(null);

  const debouncedStatsRefetch = useCallback(() => {
    if (statsDebounceRef.current) clearTimeout(statsDebounceRef.current);
    statsDebounceRef.current = setTimeout(() => {
      onStatsRefetch();
    }, STATS_DEBOUNCE_MS);
  }, [onStatsRefetch]);

  const loadGrades = useCallback(async (lessonIds: string[]) => {
    if (lessonIds.length === 0) {
      setGrades({});
      return;
    }
    
    try {
      const { data } = await api.get('/admin/journal/grades', {
        params: { lesson_ids: lessonIds }
      });
      
      const gradeMap: Record<string, Record<string, GradeData>> = {};
      for (const g of data) {
        if (!gradeMap[g.lesson_id]) gradeMap[g.lesson_id] = {};
        gradeMap[g.lesson_id][g.student_id] = {
          grade: g.grade,
          work_number: g.work_number,
          has_conflict: g.has_conflict,
          conflict_count: g.conflict_count,
        };
      }
      setGrades(gradeMap);
    } catch {
      toast.error('Ошибка загрузки оценок');
    }
  }, []);

  const loadAttestationScores = useCallback(async (
    groupId: string,
    period: AttestationPeriod,
    subjectId?: string
  ) => {
    if (period === 'all') {
      setAttestationScores({});
      return;
    }
    
    try {
      const attestationData = await AttestationAPI.calculateGroup(
        groupId,
        period as AttestationType,
        subjectId && subjectId !== 'all' ? subjectId : undefined
      );
      const scoresMap: Record<string, AttestationResult> = {};
      for (const student of attestationData.students) {
        scoresMap[student.student_id] = student;
      }
      setAttestationScores(scoresMap);
    } catch {
      toast.error('Ошибка загрузки баллов аттестации');
      setAttestationScores({});
    }
  }, []);

  const updateGrade = useCallback(async (
    lessonId: string,
    studentId: string,
    grade: number | null,
    workNumber: number | null = null
  ) => {
    let prevGrade: GradeData | undefined;

    setGrades(prev => {
      prevGrade = prev[lessonId]?.[studentId];

      if (grade === null) {
        const updated = { ...prev };
        if (updated[lessonId]) {
          const nextLessonGrades: Record<string, GradeData> = { ...updated[lessonId] };
          delete nextLessonGrades[studentId];
          updated[lessonId] = nextLessonGrades;
        }
        return updated;
      }

      return {
        ...prev,
        [lessonId]: {
          ...prev[lessonId],
          [studentId]: {
            grade,
            work_number: workNumber,
            has_conflict: false,
            conflict_count: 1,
          },
        },
      };
    });
    
    setIsSaving(true);
    try {
      if (grade === null) {
        await api.delete('/admin/journal/grades', {
          params: { lesson_id: lessonId, student_id: studentId }
        });
        debouncedStatsRefetch();
      } else {
        await api.post('/admin/journal/grades', {
          lesson_id: lessonId,
          student_id: studentId,
          grade,
          work_number: workNumber
        });
        debouncedStatsRefetch();
      }
    } catch {
      // Откат при ошибке
      if (prevGrade !== undefined) {
        const restoredGrade = prevGrade;
        setGrades(prev => {
          const nextLessonGrades: Record<string, GradeData> = { ...(prev[lessonId] ?? {}) };
          nextLessonGrades[studentId] = restoredGrade;
          return {
            ...prev,
            [lessonId]: nextLessonGrades,
          };
        });
      } else {
        setGrades(prev => {
          const updated = { ...prev };
          if (updated[lessonId]) {
            const nextLessonGrades: Record<string, GradeData> = { ...updated[lessonId] };
            delete nextLessonGrades[studentId];
            updated[lessonId] = nextLessonGrades;
          }
          return updated;
        });
      }
      toast.error('Ошибка обновления оценки');
    } finally {
      setIsSaving(false);
    }
  }, [debouncedStatsRefetch]);

  return {
    grades,
    setGrades,
    attestationScores,
    setAttestationScores,
    updateGrade,
    loadGrades,
    loadAttestationScores,
    isSaving,
  };
}
