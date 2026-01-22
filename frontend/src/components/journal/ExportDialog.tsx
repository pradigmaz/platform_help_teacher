'use client';

/**
 * Диалог экспорта журнала.
 * Позволяет выбрать период, формат и данные для экспорта.
 */

import { useState } from 'react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { CalendarIcon, Download, FileSpreadsheet } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Label } from '@/components/ui/label';

import {
  useJournalExport,
  type ExportPeriodType,
  type ExportFormat,
} from '@/hooks/useJournalExport';

interface ExportDialogProps {
  groupId: string;
  groupName?: string;
  isOpen: boolean;
  onClose: () => void;
}

/** Хелпер для ISO недели */
function getISOWeek(date: Date): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

export function ExportDialog({ groupId, groupName, isOpen, onClose }: ExportDialogProps) {
  const [periodType, setPeriodType] = useState<ExportPeriodType>('semester');
  const [exportFormat, setExportFormat] = useState<ExportFormat>('xlsx');
  const [includeAttendance, setIncludeAttendance] = useState(true);
  const [includeGrades, setIncludeGrades] = useState(true);
  const [startDate, setStartDate] = useState<Date | undefined>();
  const [endDate, setEndDate] = useState<Date | undefined>();

  const { exportJournal, isLoading, error } = useJournalExport();

  const getPeriodValue = (): string | undefined => {
    if (periodType === 'semester') return undefined;

    if (periodType === 'custom' && startDate && endDate) {
      return `${format(startDate, 'yyyy-MM-dd')}:${format(endDate, 'yyyy-MM-dd')}`;
    }

    const now = new Date();
    if (periodType === 'day') return format(now, 'yyyy-MM-dd');
    if (periodType === 'week') {
      const weekNum = getISOWeek(now);
      return `${now.getFullYear()}-W${weekNum.toString().padStart(2, '0')}`;
    }
    if (periodType === 'month') return format(now, 'yyyy-MM');

    return undefined;
  };

  const handleExport = async () => {
    await exportJournal({
      groupId,
      periodType,
      periodValue: getPeriodValue(),
      format: exportFormat,
      includeAttendance,
      includeGrades,
    });

    if (!error) onClose();
  };

  const canExport = includeAttendance || includeGrades;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            Экспорт журнала
          </DialogTitle>
          {groupName && (
            <p className="text-sm text-muted-foreground">Группа: {groupName}</p>
          )}
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Период */}
          <div className="space-y-2">
            <Label>Период</Label>
            <Select value={periodType} onValueChange={(v) => setPeriodType(v as ExportPeriodType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="semester">Семестр</SelectItem>
                <SelectItem value="month">Текущий месяц</SelectItem>
                <SelectItem value="week">Текущая неделя</SelectItem>
                <SelectItem value="day">Сегодня</SelectItem>
                <SelectItem value="custom">Произвольный период</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Выбор дат для custom */}
          {periodType === 'custom' && (
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-2">
                <Label>С</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left font-normal">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {startDate ? format(startDate, 'dd.MM.yyyy', { locale: ru }) : 'Выбрать'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar mode="single" selected={startDate} onSelect={setStartDate} locale={ru} />
                  </PopoverContent>
                </Popover>
              </div>
              <div className="space-y-2">
                <Label>По</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left font-normal">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {endDate ? format(endDate, 'dd.MM.yyyy', { locale: ru }) : 'Выбрать'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar mode="single" selected={endDate} onSelect={setEndDate} locale={ru} />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          )}

          {/* Формат */}
          <div className="space-y-2">
            <Label>Формат</Label>
            <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as ExportFormat)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="xlsx">Excel (.xlsx)</SelectItem>
                <SelectItem value="csv">CSV (.csv)</SelectItem>
                <SelectItem value="json">JSON (.json)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Данные */}
          <div className="space-y-2">
            <Label>Данные</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="attendance"
                  checked={includeAttendance}
                  onCheckedChange={(checked) => setIncludeAttendance(checked === true)}
                />
                <label htmlFor="attendance" className="text-sm cursor-pointer">
                  Посещаемость
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="grades"
                  checked={includeGrades}
                  onCheckedChange={(checked) => setIncludeGrades(checked === true)}
                />
                <label htmlFor="grades" className="text-sm cursor-pointer">
                  Оценки
                </label>
              </div>
            </div>
          </div>

          {/* Ошибка */}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Отмена
          </Button>
          <Button onClick={handleExport} disabled={isLoading || !canExport}>
            {isLoading ? (
              'Генерация...'
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Скачать
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
