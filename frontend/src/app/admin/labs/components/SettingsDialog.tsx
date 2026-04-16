'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { LabSettings } from '@/lib/api/types/labs';
import { Settings } from 'lucide-react';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  settings: LabSettings;
  setSettings: React.Dispatch<React.SetStateAction<LabSettings>>;
  onSave: () => void;
  isInitialSetup?: boolean;
}

function getNumberValue(value: string, fallback: number) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function getNullableNumberValue(value: string) {
  if (value.trim() === '') {
    return null;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

export function SettingsDialog({ open, onOpenChange, settings, setSettings, onSave, isInitialSetup }: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            {isInitialSetup ? 'Настройка лабораторных' : 'Настройки лабораторных'}
          </DialogTitle>
          <DialogDescription>
            {isInitialSetup 
              ? 'Укажите общее количество лабораторных и квоту мест на автомат для начала работы.'
              : 'Здесь задаются общее количество лабораторных и квота мест на автомат.'}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="labs_count">Общее количество лабораторных</Label>
            <Input
              id="labs_count"
              type="number"
              min={1}
              max={50}
              value={settings.labs_count}
              onChange={(e) => setSettings({
                ...settings,
                labs_count: getNumberValue(e.target.value, 10),
              })}
            />
            <p className="text-xs text-muted-foreground">
              Используется как общий total для аттестаций и автомата.
            </p>
          </div>
          <div className="grid gap-2">
            <div className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/30 px-3 py-3">
              <div className="space-y-1">
                <Label htmlFor="automatic_enabled">Автоматы включены</Label>
                <p className="text-xs text-muted-foreground">
                  Если выключить, автоматы не раздаются и в student UI показывается режим без автоматов.
                </p>
              </div>
              <Switch
                id="automatic_enabled"
                checked={settings.automatic_enabled}
                onCheckedChange={(checked) => setSettings({
                  ...settings,
                  automatic_enabled: checked,
                })}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="automatic_places">Мест на автомат</Label>
            <Input
              id="automatic_places"
              type="number"
              min={0}
              max={1000}
              disabled={!settings.automatic_enabled}
              value={settings.automatic_places ?? ''}
              onChange={(e) => setSettings({
                ...settings,
                automatic_places: getNullableNumberValue(e.target.value),
              })}
              placeholder="Без квоты"
            />
            <p className="text-xs text-muted-foreground">
              Квота хранится глобально. Когда автоматы включены, места получают те, кто раньше всех закроют все лабы.
            </p>
          </div>
        </div>
        <DialogFooter>
          {!isInitialSetup && <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>}
          <Button onClick={onSave}>{isInitialSetup ? 'Начать работу' : 'Сохранить'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
