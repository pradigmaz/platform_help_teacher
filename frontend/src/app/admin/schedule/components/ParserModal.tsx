'use client';

import { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { ScheduleAPI, ParseScheduleResponse } from '@/lib/api';
import { toast } from '@/components/ui/sonner';

interface ParserModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ParserModal({ open, onOpenChange, onSuccess }: ParserModalProps) {
  const [teacher, setTeacher] = useState('Миронов Г.Д.');
  const [startDate, setStartDate] = useState('2025-09-01');
  const [endDate, setEndDate] = useState('2025-12-31');
  const [isParsing, setIsParsing] = useState(false);
  const [result, setResult] = useState<ParseScheduleResponse | null>(null);

  const handleParse = async () => {
    if (!teacher || !startDate || !endDate) {
      toast.error('Заполните все поля');
      return;
    }
    
    setIsParsing(true);
    setResult(null);
    
    try {
      const data = await ScheduleAPI.parseSchedule(teacher, startDate, endDate);
      setResult(data);
      toast.success(`Спарсено ${data.lessons_created} занятий`);
      onSuccess?.();
    } catch (e: unknown) {
      const error = e as { response?: { data?: { detail?: string } } };
      toast.error(error?.response?.data?.detail || 'Ошибка парсинга');
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Парсинг расписания
          </DialogTitle>
          <DialogDescription>
            Загрузка расписания с kis.vgltu.ru
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label>ФИО преподавателя</Label>
            <Input
              value={teacher}
              onChange={(e) => setTeacher(e.target.value)}
              placeholder="Миронов Г.Д."
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Дата начала</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Дата окончания</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          
          {result && (
            <div className="p-3 rounded-lg bg-muted text-sm space-y-1">
              <div>Спарсено: <strong>{result.total_parsed}</strong></div>
              <div>Создано занятий: <strong>{result.lessons_created}</strong></div>
              <div>Пропущено: <strong>{result.lessons_skipped}</strong></div>
              <div>Группы: <strong>{result.groups.join(', ')}</strong></div>
              {result.subjects && result.subjects.length > 0 && (
                <div>Предметы: <strong>{result.subjects.join(', ')}</strong></div>
              )}
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Закрыть
          </Button>
          <Button onClick={handleParse} disabled={isParsing}>
            {isParsing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Парсинг...
              </>
            ) : (
              'Парсить'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
