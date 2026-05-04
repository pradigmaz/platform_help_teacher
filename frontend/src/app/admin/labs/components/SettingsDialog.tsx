'use client';

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
import { AlertTriangle, Settings } from 'lucide-react';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  settings: LabSettings;
  onOpenOfferingPolicies: () => void;
}

export function SettingsDialog({ open, onOpenChange, settings, onOpenOfferingPolicies }: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Legacy-настройки лабораторных
          </DialogTitle>
          <DialogDescription>
            Эти значения больше не редактируются как активная правда. Рабочие пороги задаются по связке группа / предмет / семестр.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="font-medium">Readonly fallback на время rollout</div>
              <div className="text-xs opacity-90">
                Если у связки ещё нет policy row, backend может подставить эти legacy-значения. Новые изменения вносятся только в настройках связок.
              </div>
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="labs_count">Legacy total лабораторных</Label>
            <Input id="labs_count" type="number" value={settings.labs_count} readOnly className="bg-muted" />
            <p className="text-xs text-muted-foreground">
              Историческое значение. Активный total теперь хранится в policy выбранного предмета.
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
                disabled
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
              readOnly
              disabled={!settings.automatic_enabled}
              value={settings.automatic_places ?? ''}
              placeholder="Без квоты"
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              Legacy-квота хранится глобально и больше не должна правиться с этой страницы.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Закрыть</Button>
          <Button
            onClick={() => {
              onOpenChange(false);
              onOpenOfferingPolicies();
            }}
          >
            Настроить по предметам здесь
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
