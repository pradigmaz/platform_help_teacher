'use client';

import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { JournalStats } from '../lib/journal-constants';

export interface UseJournalStatsReturn {
  stats: JournalStats | null;
  setStats: React.Dispatch<React.SetStateAction<JournalStats | null>>;
  loadStats: (groupId: string, startDate: string, endDate: string, subjectId?: string) => Promise<void>;
  refetchStats: () => Promise<void>;
}

interface UseJournalStatsProps {
  selectedGroupId: string;
  selectedSubjectId: string;
  startDate: string;
  endDate: string;
  lessonsCount: number;
}

export function useJournalStats({
  selectedGroupId,
  selectedSubjectId,
  startDate,
  endDate,
  lessonsCount
}: UseJournalStatsProps): UseJournalStatsReturn {
  const [stats, setStats] = useState<JournalStats | null>(null);

  const loadStats = useCallback(async (
    groupId: string,
    startDate: string,
    endDate: string,
    subjectId?: string
  ) => {
    try {
      const { data } = await api.get('/admin/journal/stats', {
        params: {
          group_id: groupId,
          start_date: startDate,
          end_date: endDate,
          ...(subjectId && subjectId !== 'all' && { subject_id: subjectId })
        }
      });
      setStats(data);
    } catch {
      toast.error('Ошибка загрузки статистики');
      setStats(null);
    }
  }, []);

  const refetchStats = useCallback(async () => {
    if (!selectedGroupId || lessonsCount === 0 || !startDate || !endDate) return;
    try {
      const { data } = await api.get('/admin/journal/stats', {
        params: {
          group_id: selectedGroupId,
          start_date: startDate,
          end_date: endDate,
          ...(selectedSubjectId !== 'all' && { subject_id: selectedSubjectId })
        }
      });
      setStats(data);
    } catch {
      toast.error('Ошибка обновления статистики');
    }
  }, [selectedGroupId, selectedSubjectId, startDate, endDate, lessonsCount]);

  return { stats, setStats, loadStats, refetchStats };
}
