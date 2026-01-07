'use client';

import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import api from '@/lib/api';

export interface UseJournalAttendanceReturn {
  attendance: Record<string, Record<string, string>>;
  setAttendance: React.Dispatch<React.SetStateAction<Record<string, Record<string, string>>>>;
  updateAttendance: (lessonId: string, studentId: string, status: string | null) => Promise<void>;
  loadAttendance: (groupId: string, lessonIds: string[]) => Promise<void>;
  isSaving: boolean;
}

interface UseJournalAttendanceProps {
  onStatsRefetch: () => void;
}

const STATS_DEBOUNCE_MS = 300;

export function useJournalAttendance({ onStatsRefetch }: UseJournalAttendanceProps): UseJournalAttendanceReturn {
  const [attendance, setAttendance] = useState<Record<string, Record<string, string>>>({});
  const [isSaving, setIsSaving] = useState(false);
  const statsDebounceRef = useRef<NodeJS.Timeout | null>(null);

  const debouncedStatsRefetch = useCallback(() => {
    if (statsDebounceRef.current) clearTimeout(statsDebounceRef.current);
    statsDebounceRef.current = setTimeout(() => {
      onStatsRefetch();
    }, STATS_DEBOUNCE_MS);
  }, [onStatsRefetch]);

  const loadAttendance = useCallback(async (groupId: string, lessonIds: string[]) => {
    if (lessonIds.length === 0) {
      setAttendance({});
      return;
    }
    
    try {
      const { data } = await api.get('/admin/journal/attendance', {
        params: { group_id: groupId, lesson_ids: lessonIds }
      });
      
      const attMap: Record<string, Record<string, string>> = {};
      for (const a of data) {
        if (!attMap[a.lesson_id]) attMap[a.lesson_id] = {};
        attMap[a.lesson_id][a.student_id] = a.status;
      }
      setAttendance(attMap);
    } catch {
      toast.error('Ошибка загрузки посещаемости');
    }
  }, []);

  const updateAttendance = useCallback(async (lessonId: string, studentId: string, status: string | null) => {
    // Optimistic update — сохраняем предыдущее значение для отката
    const prevStatus = attendance[lessonId]?.[studentId];
    
    // Сразу обновляем UI
    if (status === null) {
      setAttendance(prev => {
        const updated = { ...prev };
        if (updated[lessonId]) delete updated[lessonId][studentId];
        return updated;
      });
    } else {
      setAttendance(prev => ({
        ...prev,
        [lessonId]: { ...prev[lessonId], [studentId]: status }
      }));
    }
    
    setIsSaving(true);
    try {
      if (status === null) {
        await api.delete('/admin/journal/attendance', {
          params: { lesson_id: lessonId, student_id: studentId }
        });
      } else {
        await api.post('/admin/journal/attendance/bulk', {
          lesson_id: lessonId,
          records: [{ student_id: studentId, status }]
        });
      }
      debouncedStatsRefetch();
    } catch {
      // Откат при ошибке
      if (prevStatus) {
        setAttendance(prev => ({
          ...prev,
          [lessonId]: { ...prev[lessonId], [studentId]: prevStatus }
        }));
      } else {
        setAttendance(prev => {
          const updated = { ...prev };
          if (updated[lessonId]) delete updated[lessonId][studentId];
          return updated;
        });
      }
      toast.error('Ошибка обновления посещаемости');
    } finally {
      setIsSaving(false);
    }
  }, [attendance, debouncedStatsRefetch]);

  return { attendance, setAttendance, updateAttendance, loadAttendance, isSaving };
}
