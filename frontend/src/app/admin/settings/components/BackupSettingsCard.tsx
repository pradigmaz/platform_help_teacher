'use client';

import { useState } from 'react';
import { Save, Loader2, Clock, Database, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { BackupSettings, BackupSettingsUpdate } from '@/lib/api';

interface BackupSettingsCardProps {
  settings: BackupSettings;
  isSaving: boolean;
  onSave: (data: BackupSettingsUpdate) => void;
}

export function BackupSettingsCard({ settings, isSaving, onSave }: BackupSettingsCardProps) {
  const [form, setForm] = useState<BackupSettings>({
    enabled: settings?.enabled ?? true,
    schedule_hour: settings?.schedule_hour ?? 3,
    schedule_minute: settings?.schedule_minute ?? 0,
    retention_days: settings?.retention_days ?? 30,
    max_backups: settings?.max_backups ?? 10,
    storage_bucket: settings?.storage_bucket ?? 'edu-backups',
    notify_on_success: settings?.notify_on_success ?? false,
    notify_on_failure: settings?.notify_on_failure ?? true,
  });

  const handleSave = () => {
    onSave({
      enabled: form.enabled,
      schedule_hour: form.schedule_hour,
      schedule_minute: form.schedule_minute,
      retention_days: form.retention_days,
      max_backups: form.max_backups,
      notify_on_success: form.notify_on_success,
      notify_on_failure: form.notify_on_failure,
    });
  };

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-500/10">
            <Database className="h-5 w-5 text-green-500" />
          </div>
          <div>
            <CardTitle className="text-lg">Автоматическое резервное копирование</CardTitle>
            <CardDescription>Настройки автоматического создания бэкапов</CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Enable/Disable */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Автобэкап включён</Label>
            <p className="text-xs text-muted-foreground">Бэкапы создаются автоматически по расписанию</p>
          </div>
          <Switch
            checked={form.enabled}
            onCheckedChange={(checked) => setForm({ ...form, enabled: checked })}
          />
        </div>

        {/* Schedule */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <Label>Время бэкапа</Label>
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              min={0}
              max={23}
              value={form.schedule_hour}
              onChange={(e) => setForm({ ...form, schedule_hour: parseInt(e.target.value) || 0 })}
              className="w-20"
            />
            <span className="text-muted-foreground">:</span>
            <Input
              type="number"
              min={0}
              max={59}
              value={form.schedule_minute}
              onChange={(e) => setForm({ ...form, schedule_minute: parseInt(e.target.value) || 0 })}
              className="w-20"
            />
            <span className="text-sm text-muted-foreground ml-2">(по МСК)</span>
          </div>
        </div>

        {/* Retention */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Хранить дней</Label>
            <Input
              type="number"
              min={1}
              max={365}
              value={form.retention_days}
              onChange={(e) => setForm({ ...form, retention_days: parseInt(e.target.value) || 30 })}
            />
          </div>
          <div className="space-y-2">
            <Label>Макс. бэкапов</Label>
            <Input
              type="number"
              min={1}
              max={100}
              value={form.max_backups}
              onChange={(e) => setForm({ ...form, max_backups: parseInt(e.target.value) || 10 })}
            />
          </div>
        </div>

        {/* Notifications */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <Label>Уведомления в Telegram</Label>
          </div>
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <Label className="font-normal">При успешном бэкапе (+ файл)</Label>
              <Switch
                checked={form.notify_on_success}
                onCheckedChange={(checked) => setForm({ ...form, notify_on_success: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label className="font-normal">При ошибке бэкапа</Label>
              <Switch
                checked={form.notify_on_failure}
                onCheckedChange={(checked) => setForm({ ...form, notify_on_failure: checked })}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Сохранение...</>
            ) : (
              <><Save className="mr-2 h-4 w-4" />Сохранить</>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
