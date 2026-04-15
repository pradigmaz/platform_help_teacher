/**
 * Хук для экспорта журнала.
 */
import { useState, useCallback } from 'react';
import api from '@/lib/api';

export type ExportPeriodType = 'day' | 'week' | 'month' | 'semester' | 'custom';
export type ExportFormat = 'xlsx' | 'csv' | 'json';
export type ExportSubgroup = 1 | 2;

export interface ExportParams {
  groupId: string;
  subgroup?: ExportSubgroup;
  studentId?: string;
  periodType?: ExportPeriodType;
  periodValue?: string;
  format?: ExportFormat;
  includeAttendance?: boolean;
  includeGrades?: boolean;
}

interface UseJournalExportReturn {
  exportJournal: (params: ExportParams) => Promise<boolean>;
  isLoading: boolean;
  error: string | null;
}

function getFilenameFromContentDisposition(contentDisposition?: string): string | null {
  if (!contentDisposition) {
    return null;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      // Fall back to the plain filename attribute below.
    }
  }

  const plainMatch = contentDisposition.match(/filename="?([^"]+)"?/i);
  return plainMatch?.[1] ?? null;
}

export function useJournalExport(): UseJournalExportReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportJournal = useCallback(async (params: ExportParams) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<Blob>('/admin/journal/export', {
        params: {
          group_id: params.groupId,
          subgroup: params.subgroup,
          student_id: params.studentId,
          period_type: params.periodType,
          period_value: params.periodValue,
          format: params.format,
          include_attendance: params.includeAttendance,
          include_grades: params.includeGrades,
        },
        responseType: 'blob',
      });

      // Получаем имя файла из заголовка
      const contentDisposition = response.headers['content-disposition'];
      const filename = getFilenameFromContentDisposition(contentDisposition) ?? 'journal_export.xlsx';

      // Скачиваем файл
      const blob = response.data instanceof Blob ? response.data : new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      return true;

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Неизвестная ошибка';
      setError(message);
      console.error('Export error:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { exportJournal, isLoading, error };
}
