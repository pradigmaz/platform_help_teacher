/**
 * Хук для экспорта журнала.
 */
import { useState, useCallback } from 'react';

export type ExportPeriodType = 'day' | 'week' | 'month' | 'semester' | 'custom';
export type ExportFormat = 'xlsx' | 'csv' | 'json';

export interface ExportParams {
  groupId: string;
  periodType?: ExportPeriodType;
  periodValue?: string;
  format?: ExportFormat;
  includeAttendance?: boolean;
  includeGrades?: boolean;
}

interface UseJournalExportReturn {
  exportJournal: (params: ExportParams) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function useJournalExport(): UseJournalExportReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportJournal = useCallback(async (params: ExportParams) => {
    setIsLoading(true);
    setError(null);

    try {
      // Формируем query параметры
      const searchParams = new URLSearchParams();
      searchParams.set('group_id', params.groupId);
      
      if (params.periodType) {
        searchParams.set('period_type', params.periodType);
      }
      if (params.periodValue) {
        searchParams.set('period_value', params.periodValue);
      }
      if (params.format) {
        searchParams.set('format', params.format);
      }
      if (params.includeAttendance !== undefined) {
        searchParams.set('include_attendance', String(params.includeAttendance));
      }
      if (params.includeGrades !== undefined) {
        searchParams.set('include_grades', String(params.includeGrades));
      }

      const response = await fetch(
        `/api/v1/admin/journal/export?${searchParams.toString()}`,
        {
          method: 'GET',
          credentials: 'include',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Ошибка экспорта: ${response.status}`);
      }

      // Получаем имя файла из заголовка
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'journal_export.xlsx';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      // Скачиваем файл
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Неизвестная ошибка';
      setError(message);
      console.error('Export error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { exportJournal, isLoading, error };
}
