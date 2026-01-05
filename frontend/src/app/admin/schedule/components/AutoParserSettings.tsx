'use client';

import { useState, useEffect } from 'react';
import { Settings, Clock, Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from '@/components/ui/sonner';
import api from '@/lib/api';

interface AutoParserConfig {
  enabled: boolean;
  teacher_name: string;
  day_of_week: number;
  run_time: string;
  parse_days_ahead: number;
}

interface AutoParserSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DAYS = [
  { value: '0', label: 'Понедельник' },
  { value: '1', label: 'Вторник' },
  { value: '2', label: 'Среда' },
  { value: '3', label: 'Четверг' },
  { value: '4', label: 'Пятница' },
  { value: '5', label: 'Суббота' },
  { value: '6', label: 'Воскресенье' },
];

export function AutoParserSettings({ open, onOpenChange }: AutoParserSettingsProps) {
  const [config, setConfig] = useState<AutoParserConfig>({
    enabled: false,
    teacher_name: 'Миронов Г.Д.',
    day_of_week: 6,
    run_time: '20:00',
    parse_days_ahead: 14,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (open) {
      loadConfig();
    }
  }, [open]);

  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get('/admin/schedule/parser-config');
      if (data) {
        setConfig({
          enabled: data.enabled,
          teacher_name: data.teacher_name,
          day_of_week: data.day_of_week,
          run_time: data.run_time,
          parse_days_ahead: data.parse_days_ahead,
        });
      }
    } catch {
      // Use defaults
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.post('/admin/schedule/parser-config', config);
      toast.success('Настройки сохранены');
      onOpenChange(false);
    } catch {
      toast.error('Ошибка сохранения');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Автоматический парсинг
          </DialogTitle>
          <DialogDescription>
            Настройка автоматического обновления расписания
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="enabled">Включить автопарсинг</Label>
            <Switch
              id="enabled"
              checked={config.enabled}
              onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
            />
          </div>
          
          <div className="space-y-2">
            <Label>ФИО преподавателя</Label>
            <Input
              value={config.teacher_name}
              onChange={(e) => setConfig({ ...config, teacher_name: e.target.value })}
              placeholder="Миронов Г.Д."
              disabled={!config.enabled}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>День запуска</Label>
              <Select
                value={String(config.day_of_week)}
                onValueChange={(v) => setConfig({ ...config, day_of_week: Number(v) })}
                disabled={!config.enabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DAYS.map(day => (
                    <SelectItem key={day.value} value={day.value}>
                      {day.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Время запуска</Label>
              <Input
                type="time"
                value={config.run_time}
                onChange={(e) => setConfig({ ...config, run_time: e.target.value })}
                disabled={!config.enabled}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label>Парсить дней вперёд</Label>
            <Input
              type="number"
              min={7}
              max={60}
              value={config.parse_days_ahead}
              onChange={(e) => setConfig({ ...config, parse_days_ahead: Number(e.target.value) })}
              disabled={!config.enabled}
            />
            <p className="text-xs text-muted-foreground">
              Сколько дней вперёд от текущей даты парсить расписание
            </p>
          </div>
          
          {config.enabled && (
            <div className="p-3 rounded-lg bg-muted text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4" />
                Следующий запуск: {DAYS.find(d => d.value === String(config.day_of_week))?.label} в {config.run_time}
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Отмена
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Сохранение...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Сохранить
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
