'use client';

import { useState, useEffect } from 'react';
import { Settings, Clock, Save, Loader2, Play } from 'lucide-react';
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
import { toast } from '@/components/ui/sonner';
import api from '@/lib/api';

interface AutoParserConfig {
  enabled: boolean;
  teacher_name: string;
  days_of_week: number[];
  run_time: string;
  parse_days_ahead: number;
  last_run_at?: string;
}

interface AutoParserSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onParseNow?: () => void;
}

const DAYS = [
  { value: 0, label: 'Пн' },
  { value: 1, label: 'Вт' },
  { value: 2, label: 'Ср' },
  { value: 3, label: 'Чт' },
  { value: 4, label: 'Пт' },
  { value: 5, label: 'Сб' },
  { value: 6, label: 'Вс' },
];

export function AutoParserSettings({ open, onOpenChange, onParseNow }: AutoParserSettingsProps) {
  const [config, setConfig] = useState<AutoParserConfig>({
    enabled: false,
    teacher_name: 'Миронов Г.Д.',
    days_of_week: [6],
    run_time: '20:00',
    parse_days_ahead: 14,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
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
          days_of_week: data.days_of_week || [6],
          run_time: data.run_time,
          parse_days_ahead: data.parse_days_ahead,
          last_run_at: data.last_run_at,
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

  const handleParseNow = async () => {
    setIsParsing(true);
    try {
      await api.post('/admin/schedule/parse-now');
      toast.success('Парсинг запущен');
      onParseNow?.();
    } catch {
      toast.error('Ошибка запуска парсинга');
    } finally {
      setIsParsing(false);
    }
  };

  const toggleDay = (day: number) => {
    const newDays = config.days_of_week.includes(day)
      ? config.days_of_week.filter(d => d !== day)
      : [...config.days_of_week, day].sort((a, b) => a - b);
    
    if (newDays.length > 0) {
      setConfig({ ...config, days_of_week: newDays });
    }
  };

  const formatLastRun = (dateStr?: string) => {
    if (!dateStr) return 'Никогда';
    const date = new Date(dateStr);
    return date.toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getNextRunDays = () => {
    return config.days_of_week
      .map(d => DAYS.find(day => day.value === d)?.label)
      .filter(Boolean)
      .join(', ');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
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
          
          <div className="space-y-2">
            <Label>Дни запуска</Label>
            <div className="flex gap-1.5 justify-start">
              {DAYS.map(day => (
                <button
                  key={day.value}
                  type="button"
                  onClick={() => config.enabled && toggleDay(day.value)}
                  disabled={!config.enabled}
                  className={`w-10 h-10 rounded-md border text-sm font-medium transition-colors ${
                    config.days_of_week.includes(day.value)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background border-input hover:bg-accent'
                  } ${!config.enabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Время запуска</Label>
              <Input
                type="time"
                value={config.run_time}
                onChange={(e) => setConfig({ ...config, run_time: e.target.value })}
                disabled={!config.enabled}
                className="w-full"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Дней вперёд</Label>
              <Input
                type="number"
                min={7}
                max={60}
                value={config.parse_days_ahead}
                onChange={(e) => setConfig({ ...config, parse_days_ahead: Number(e.target.value) })}
                disabled={!config.enabled}
                className="w-full"
              />
            </div>
          </div>
          
          {config.enabled && (
            <div className="p-3 rounded-lg bg-muted text-sm space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4 shrink-0" />
                <span>Запуск: {getNextRunDays()} в {config.run_time}</span>
              </div>
              <div className="text-muted-foreground text-xs pl-6">
                Последний запуск: {formatLastRun(config.last_run_at)}
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter className="gap-2 sm:gap-2">
          <Button 
            variant="outline" 
            onClick={handleParseNow}
            disabled={isParsing || !config.teacher_name}
            size="sm"
          >
            {isParsing ? (
              <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-1.5" />
            )}
            Запустить
          </Button>
          <div className="flex-1" />
          <Button variant="outline" onClick={() => onOpenChange(false)} size="sm">
            Отмена
          </Button>
          <Button onClick={handleSave} disabled={isSaving} size="sm">
            {isSaving ? (
              <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-1.5" />
            )}
            Сохранить
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
