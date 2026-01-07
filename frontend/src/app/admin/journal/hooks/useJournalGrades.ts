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
  updateGrade: (lessonId: string, studentId: string, grade: number | null, workNumber?: number | null) => Promise<void>;
  loadGrades: (lessonIds: string[]) => Promise<void>;
  loadAttestationScores: (groupId: string, period: AttestationPeriod) => Promise<void>;
  isSaving: boolean;
}

interface UseJournalGradesProps {
  attendance: Record<string, Record<string, string>>;
  updateAttendance: (lessonId: string, studentId: string, status: string | null) => Promise<void>;
  onStatsRefetch: () => void;
}

const STATS_DEBOUNCE_MS = 300;

export function useJournalGrades({ attendance, updateAttendance, onStatsRefetch }: UseJournalGradesProps): UseJournalGradesReturn {
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
        gradeMap[g.lesson_id][g.student_id] = { grade: g.grade, work_number: g.work_number };
      }
      setGrades(gradeMap);
    } catch {
      toast.error('Ошибка загрузки оценок');
    }
  }, []);

  const loadAttestationScores = useCallback(async (groupId: string, period: AttestationPeriod) => {
    if (period === 'all') {
      setAttestationScores({});
      return;
    }
    
    try {
      const attestationData = await AttestationAPI.calculateGroup(groupId, period as AttestationType);
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
    // Optimistic update — сохраняем предыдущее значение
    const prevGrade = grades[lessonId]?.[studentId];
    
    // Сразу обновляем UI
    if (grade === null) {
      setGrades(prev => {
        const updated = { ...prev };
        if (updated[lessonId]) delete updated[lessonId][studentId];
        return updated;
      });
    } else {
      setGrades(prev => ({
        ...prev,
        [lessonId]: { ...prev[lessonId], [studentId]: { grade, work_number: workNumber } }
      }));
    }
    
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
        
        const currentStatus = attendance[lessonId]?.[studentId];
        if (!currentStatus || currentStatus === 'ABSENT') {
          await updateAttendance(lessonId, studentId, 'PRESENT');
        } else {
          debouncedStatsRefetch();
        }
      }
    } catch {
      // Откат при ошибке
      if (prevGrade) {
        setGrades(prev => ({
          ...prev,
          [lessonId]: { ...prev[lessonId], [studentId]: prevGrade }
        }));
      } else {
        setGrades(prev => {
          const updated = { ...prev };
          if (updated[lessonId]) delete updated[lessonId][studentId];
          return updated;
        });
      }
      toast.error('Ошибка обновления оценки');
    } finally {
      setIsSaving(false);
    }
  }, [grades, attendance, updateAttendance, debouncedStatsRefetch]);

  return { grades, setGrades, attestationScores, updateGrade, loadGrades, loadAttestationScores, isSaving };
}
