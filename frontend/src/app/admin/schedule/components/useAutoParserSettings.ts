'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from '@/components/ui/sonner';
import api, {
  type ScheduleAutoParseResponse,
  type ScheduleParserConfig,
  type ScheduleParserConfigResponse,
} from '@/lib/api';

export const AUTO_PARSER_DAYS = [
  { value: 0, label: 'Пн' },
  { value: 1, label: 'Вт' },
  { value: 2, label: 'Ср' },
  { value: 3, label: 'Чт' },
  { value: 4, label: 'Пт' },
  { value: 5, label: 'Сб' },
  { value: 6, label: 'Вс' },
];

const DEFAULT_CONFIG: ScheduleParserConfig = {
  enabled: false,
  teacher_name: 'Миронов Г.Д.',
  days_of_week: [6],
  run_time: '20:00',
  parse_days_ahead: 14,
};

interface UseAutoParserSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onParseNow?: () => void;
  onParsingChange?: (isParsing: boolean) => void;
}

export function useAutoParserSettings({
  open,
  onOpenChange,
  onParseNow,
  onParsingChange,
}: UseAutoParserSettingsProps) {
  const [config, setConfig] = useState<ScheduleParserConfig>(DEFAULT_CONFIG);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [parseResult, setParseResult] = useState<ScheduleAutoParseResponse | null>(null);

  const loadConfig = useCallback(async () => {
    try {
      const { data } = await api.get<ScheduleParserConfigResponse | null>('/admin/schedule/parser-config');
      if (data) {
        setConfig({
          enabled: data.enabled,
          teacher_name: data.teacher_name,
          days_of_week: data.days_of_week || [6],
          run_time: data.run_time,
          parse_days_ahead: data.parse_days_ahead,
        });
        setLastRunAt(data.last_run_at);
        return;
      }
      setConfig(DEFAULT_CONFIG);
      setLastRunAt(null);
    } catch {
      setConfig(DEFAULT_CONFIG);
      setLastRunAt(null);
    }
  }, []);

  useEffect(() => {
    if (open) {
      void loadConfig();
      setParseResult(null);
    }
  }, [loadConfig, open]);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      const { data } = await api.post<ScheduleParserConfigResponse>('/admin/schedule/parser-config', config);
      setConfig({
        enabled: data.enabled,
        teacher_name: data.teacher_name,
        days_of_week: data.days_of_week,
        run_time: data.run_time,
        parse_days_ahead: data.parse_days_ahead,
      });
      setLastRunAt(data.last_run_at);
      toast.success('Настройки сохранены');
      onOpenChange(false);
    } catch {
      toast.error('Ошибка сохранения');
    } finally {
      setIsSaving(false);
    }
  }, [config, onOpenChange]);

  const handleParseNow = useCallback(async () => {
    setIsParsing(true);
    setParseResult(null);
    onParsingChange?.(true);
    try {
      const { data } = await api.post<ScheduleAutoParseResponse>('/admin/schedule/parse-now');
      setParseResult(data);
      await loadConfig();
      toast.success(`Создано ${data.lessons_created} занятий`);
      onParseNow?.();
    } catch (error: unknown) {
      const responseError = error as { response?: { data?: { detail?: string } } };
      toast.error(responseError?.response?.data?.detail || 'Ошибка парсинга');
    } finally {
      setIsParsing(false);
      onParsingChange?.(false);
    }
  }, [loadConfig, onParseNow, onParsingChange]);

  const toggleDay = useCallback((day: number) => {
    const nextDays = config.days_of_week.includes(day)
      ? config.days_of_week.filter((item) => item !== day)
      : [...config.days_of_week, day].sort((left, right) => left - right);

    if (nextDays.length > 0) {
      setConfig((current) => ({ ...current, days_of_week: nextDays }));
    }
  }, [config.days_of_week]);

  const formatLastRun = useCallback((dateStr?: string | null) => {
    if (!dateStr) {
      return 'Никогда';
    }
    return new Date(dateStr).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, []);

  const getNextRunDays = useCallback(() => {
    return config.days_of_week
      .map((day) => AUTO_PARSER_DAYS.find((item) => item.value === day)?.label)
      .filter(Boolean)
      .join(', ');
  }, [config.days_of_week]);

  return {
    config,
    setConfig,
    lastRunAt,
    isSaving,
    isParsing,
    parseResult,
    handleSave,
    handleParseNow,
    toggleDay,
    formatLastRun,
    getNextRunDays,
  };
}
