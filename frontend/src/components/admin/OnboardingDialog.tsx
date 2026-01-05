'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { User, Calendar, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import { Progress } from '@/components/ui/progress';

interface OnboardingDialogProps {
  open: boolean;
  onComplete: (fullName: string) => void;
}

export function OnboardingDialog({ open, onComplete }: OnboardingDialogProps) {
  const [fullName, setFullName] = useState('');
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [startDate, setStartDate] = useState('2025-09-01');
  const [saving, setSaving] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = fullName.trim();
    if (!trimmed) {
      toast.error('Введите ФИО');
      return;
    }
    
    setSaving(true);
    try {
      // Сохраняем ФИО
      await api.patch('/users/me', { full_name: trimmed });
      
      if (mode === 'auto') {
        // Запускаем парсинг
        setParsing(true);
        setProgress(10);
        
        const response = await api.post('/admin/schedule/parse', {
          teacher_name: trimmed,
          start_date: startDate,
        });
        
        setProgress(100);
        
        const data = response.data;
        toast.success(
          `Импортировано: ${data.lessons_created} занятий, ${data.groups_created} групп`
        );
      }
      
      // Завершаем onboarding
      await api.patch('/users/me', { onboarding_completed: true });
      
      onComplete(trimmed);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Ошибка сохранения';
      toast.error(message);
    } finally {
      setSaving(false);
      setParsing(false);
    }
  };

  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-[500px]" onPointerDownOutside={(e) => e.preventDefault()}>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Добро пожаловать!
            </DialogTitle>
            <DialogDescription>
              Настройте платформу для работы с расписанием
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            {/* ФИО */}
            <div className="grid gap-2">
              <Label htmlFor="fullName">ФИО преподавателя</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Миронов Г.Д."
                autoFocus
                disabled={saving}
              />
              <p className="text-xs text-muted-foreground">
                Формат: Фамилия И.О. (как на сайте расписания)
              </p>
            </div>

            {/* Режим */}
            <div className="grid gap-2">
              <Label>Расписание</Label>
              <RadioGroup value={mode} onValueChange={(v) => setMode(v as 'auto' | 'manual')} disabled={saving}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="auto" id="auto" />
                  <Label htmlFor="auto" className="font-normal cursor-pointer">
                    Загрузить автоматически с сайта ВГЛТУ
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="manual" id="manual" />
                  <Label htmlFor="manual" className="font-normal cursor-pointer">
                    Создать вручную позже
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Дата начала (только для авто) */}
            {mode === 'auto' && (
              <div className="grid gap-2">
                <Label htmlFor="startDate" className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Дата начала семестра
                </Label>
                <Input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  disabled={saving}
                />
                <p className="text-xs text-muted-foreground">
                  Расписание будет загружено с этой даты по сегодня
                </p>
              </div>
            )}

            {/* Прогресс парсинга */}
            {parsing && (
              <div className="grid gap-2">
                <Label>Загрузка расписания...</Label>
                <Progress value={progress} />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="submit" disabled={saving || !fullName.trim()}>
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {parsing ? 'Загрузка...' : 'Сохранение...'}
                </>
              ) : (
                'Продолжить'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
