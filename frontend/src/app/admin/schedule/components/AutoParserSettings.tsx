'use client';

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
import { AUTO_PARSER_DAYS, useAutoParserSettings } from './useAutoParserSettings';

interface AutoParserSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onParseNow?: () => void;
  onParsingChange?: (isParsing: boolean) => void;
}

export function AutoParserSettings({ open, onOpenChange, onParseNow, onParsingChange }: AutoParserSettingsProps) {
  const {
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
  } = useAutoParserSettings({
    open,
    onOpenChange,
    onParseNow,
    onParsingChange,
  });

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
              {AUTO_PARSER_DAYS.map(day => (
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
                Последний запуск: {formatLastRun(lastRunAt)}
              </div>
            </div>
          )}
          
          {parseResult && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-sm space-y-1">
              <div className="font-medium text-green-600 dark:text-green-400">
                ✓ Парсинг завершён
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-muted-foreground text-xs">
                <span>Найдено: <strong>{parseResult.total_parsed}</strong></span>
                <span>Создано: <strong>{parseResult.lessons_created}</strong></span>
                {parseResult.lessons_updated > 0 && (
                  <span>Обновлено: <strong>{parseResult.lessons_updated}</strong></span>
                )}
                <span>Пропущено: <strong>{parseResult.lessons_skipped}</strong></span>
                {parseResult.conflicts_created > 0 && (
                  <span className="text-yellow-600">Конфликтов: <strong>{parseResult.conflicts_created}</strong></span>
                )}
              </div>
            </div>
          )}
          
          {isParsing && (
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-sm">
              <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Парсинг расписания...</span>
              </div>
              <div className="text-muted-foreground text-xs mt-1">
                Загрузка данных с kis.vgltu.ru
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
