'use client';

import { useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Loader2, Clock, Database, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { BackupSettings, BackupSettingsUpdate } from '@/lib/api';
import { backupSettingsSchema, type BackupSettingsFormValues } from './backup-settings-schema';

interface BackupSettingsCardProps {
  settings: BackupSettings;
  isSaving: boolean;
  onSave: (data: BackupSettingsUpdate) => void;
}

export function BackupSettingsCard({ settings, isSaving, onSave }: BackupSettingsCardProps) {
  const form = useForm<BackupSettingsFormValues>({
    resolver: zodResolver(backupSettingsSchema),
    mode: 'onChange',
    defaultValues: {
      enabled: settings?.enabled ?? true,
      schedule_hour: settings?.schedule_hour ?? 17,
      schedule_minute: settings?.schedule_minute ?? 0,
      retention_days: settings?.retention_days ?? 30,
      max_backups: settings?.max_backups ?? 10,
      notify_on_success: settings?.notify_on_success ?? false,
      notify_on_failure: settings?.notify_on_failure ?? true,
    },
  });
  const enabled = useWatch({ control: form.control, name: 'enabled' });
  const notifyOnSuccess = useWatch({ control: form.control, name: 'notify_on_success' });
  const notifyOnFailure = useWatch({ control: form.control, name: 'notify_on_failure' });

  useEffect(() => {
    form.reset({
      enabled: settings?.enabled ?? true,
      schedule_hour: settings?.schedule_hour ?? 17,
      schedule_minute: settings?.schedule_minute ?? 0,
      retention_days: settings?.retention_days ?? 30,
      max_backups: settings?.max_backups ?? 10,
      notify_on_success: settings?.notify_on_success ?? false,
      notify_on_failure: settings?.notify_on_failure ?? true,
    });
  }, [form, settings]);

  useEffect(() => {
    console.log('[BackupSettingsCard] Form errors:', form.formState.errors);
  }, [form.formState.errors]);

  const handleSave = form.handleSubmit((values) => {
    console.log('[BackupSettingsCard] Submitting:', values);
    onSave(values);
  });

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-green-500/10 p-2">
            <Database className="h-5 w-5 text-green-500" />
          </div>
          <div>
            <CardTitle className="text-lg">Автоматическое резервное копирование</CardTitle>
            <CardDescription>Настройки автоматического создания бэкапов</CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Автобэкап включён</Label>
            <p className="text-xs text-muted-foreground">Бэкапы создаются автоматически по расписанию</p>
          </div>
          <Switch checked={enabled} onCheckedChange={(checked) => form.setValue('enabled', checked)} />
        </div>

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
              {...form.register('schedule_hour', { valueAsNumber: true })}
              className="w-20"
            />
            <span className="text-muted-foreground">:</span>
            <Input
              type="number"
              min={0}
              max={59}
              {...form.register('schedule_minute', { valueAsNumber: true })}
              className="w-20"
            />
            <span className="ml-2 text-sm text-muted-foreground">(по МСК)</span>
          </div>
          {(form.formState.errors.schedule_hour || form.formState.errors.schedule_minute) && (
            <p className="text-xs text-destructive">
              {form.formState.errors.schedule_hour?.message || form.formState.errors.schedule_minute?.message}
            </p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Хранить дней</Label>
            <Input type="number" min={1} max={365} {...form.register('retention_days', { valueAsNumber: true })} />
            {form.formState.errors.retention_days && (
              <p className="text-xs text-destructive">{form.formState.errors.retention_days.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label>Макс. бэкапов</Label>
            <Input type="number" min={1} max={100} {...form.register('max_backups', { valueAsNumber: true })} />
            {form.formState.errors.max_backups && (
              <p className="text-xs text-destructive">{form.formState.errors.max_backups.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <Label>Уведомления в Telegram</Label>
          </div>
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <Label className="font-normal">При успешном бэкапе (+ зашифрованный файл)</Label>
              <Switch checked={notifyOnSuccess} onCheckedChange={(checked) => form.setValue('notify_on_success', checked)} />
            </div>
            <div className="flex items-center justify-between">
              <Label className="font-normal">При ошибке бэкапа</Label>
              <Switch checked={notifyOnFailure} onCheckedChange={(checked) => form.setValue('notify_on_failure', checked)} />
            </div>
          </div>
        </div>

        <div className="flex justify-end border-t pt-4">
          <Button onClick={handleSave} disabled={isSaving || !form.formState.isValid}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Сохранение...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Сохранить
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
