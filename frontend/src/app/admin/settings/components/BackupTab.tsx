'use client';

import { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { Copy, ShieldCheck, TriangleAlert } from 'lucide-react';
import { toast } from 'sonner';
import {
  ApiError,
  BackupAPI,
  type BackupCreateResponse,
  type BackupHealthResponse,
  type BackupInfo,
  type BackupSettings,
  type BackupSettingsUpdate,
  type RestoreResponse,
  type UploadBackupResponse,
  type VerifyResponse,
} from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { BackupListCard } from './BackupListCard';
import { BackupSettingsCard } from './BackupSettingsCard';

const DEFAULT_SETTINGS: BackupSettings = {
  enabled: true,
  schedule_hour: 17,
  schedule_minute: 0,
  retention_days: 30,
  max_backups: 10,
  notify_on_success: false,
  notify_on_failure: true,
};

function getVerifyMessage(result: VerifyResponse): string {
  switch (result.status) {
    case 'valid':
      return 'Бэкап валиден';
    case 'recovery_code_required':
      return result.error || 'Для проверки этого бэкапа нужен recovery code';
    case 'invalid_recovery_code':
      return result.error || 'Recovery code неверный';
    case 'dump_invalid':
      return result.error || 'Бэкап расшифровался, но dump не читается через pg_restore';
    default:
      return result.error || 'Проверка бэкапа завершилась ошибкой';
  }
}

function getRestoreMessage(result: RestoreResponse): string {
  if (result.success) {
    return 'База данных восстановлена';
  }
  switch (result.status) {
    case 'recovery_code_required':
      return result.error || 'Для восстановления этого бэкапа нужен recovery code';
    case 'invalid_recovery_code':
      return result.error || 'Recovery code неверный';
    default:
      return result.error || 'Восстановление завершилось ошибкой';
  }
}

function getUploadMessage(result: UploadBackupResponse): string {
  if (!result.success) {
    return result.error || 'Ошибка загрузки бэкапа';
  }
      if (result.verification_status === 'recovery_code_required') {
        return 'Файл загружен. Для полной проверки на этой машине понадобится recovery code.';
      }
      if (result.verified === false) {
        return result.error || 'Файл загружен, но полная проверка не прошла';
  }
  return `Бэкап загружен: ${result.backup_key}`;
}

function getCreateMessage(result: BackupCreateResponse): string {
  if (!result.success) {
    return result.error || 'Ошибка создания бэкапа';
  }
  if (result.mirrored_offsite === false) {
    return `Бэкап создан: ${result.backup_key}. Offsite mirror не удался.`;
  }
  return `Бэкап создан: ${result.backup_key}`;
}

export function BackupTab() {
  const [latestPortableBackup, setLatestPortableBackup] = useState<{ backupKey: string; recoveryCode: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [settings, setSettings] = useState<BackupSettings>(DEFAULT_SETTINGS);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [health, setHealth] = useState<BackupHealthResponse | null>(null);

  const handleCopyRecoveryCode = useCallback(async () => {
    if (!latestPortableBackup) {
      return;
    }
    try {
      await navigator.clipboard.writeText(latestPortableBackup.recoveryCode);
      toast.success('Recovery code скопирован');
    } catch (error) {
      console.error('Failed to copy recovery code:', error);
      toast.error('Не удалось скопировать recovery code');
    }
  }, [latestPortableBackup]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [settingsResult, backupsResult, healthResult] = await Promise.allSettled([
        BackupAPI.getSettings(),
        BackupAPI.list(),
        BackupAPI.health(),
      ]);
      if (settingsResult.status === 'fulfilled') {
        setSettings(settingsResult.value);
      }
      if (backupsResult.status === 'fulfilled') {
        setBackups(backupsResult.value?.backups || []);
      }
      if (healthResult.status === 'fulfilled') {
        setHealth(healthResult.value);
      } else {
        setHealth(null);
      }
      if (settingsResult.status === 'rejected') {
        throw settingsResult.reason;
      }
      if (backupsResult.status === 'rejected') {
        throw backupsResult.reason;
      }
    } catch (error) {
      console.error('Failed to load backup data:', error);
      toast.error('Ошибка загрузки данных бэкапов');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleSaveSettings = async (data: BackupSettingsUpdate) => {
    setIsSaving(true);
    try {
      const updated = await BackupAPI.updateSettings(data);
      setSettings(updated);
      toast.success('Настройки сохранены');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Ошибка сохранения настроек');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateBackup = async () => {
    setIsCreating(true);
    try {
      const result = await BackupAPI.create();
      if (!result.success) {
        toast.error(getCreateMessage(result));
        return;
      }
      toast.success(getCreateMessage(result));
      if (result.backup_key && result.recovery_code) {
        setLatestPortableBackup({ backupKey: result.backup_key, recoveryCode: result.recovery_code });
      } else {
        setLatestPortableBackup(null);
      }
      if (result.notification_sent === false) {
        toast(result.notification_error || 'Бэкап создан, но отправка уведомления не удалась');
      }
      if (result.offsite_error) {
        toast(result.offsite_error);
      }
      await loadData();
    } catch (error) {
      console.error('Failed to create backup:', error);
      toast.error('Ошибка создания бэкапа');
    } finally {
      setIsCreating(false);
    }
  };

  const handleVerify = async (key: string, recoveryCode?: string): Promise<VerifyResponse | null> => {
    try {
      const result = await BackupAPI.verify(key, recoveryCode);
      if (result.valid) {
        toast.success(getVerifyMessage(result));
      } else if (result.status === 'recovery_code_required') {
        toast(getVerifyMessage(result));
      } else {
        toast.error(getVerifyMessage(result));
      }
      return result;
    } catch (error) {
      console.error('Failed to verify backup:', error);
      toast.error('Ошибка проверки бэкапа');
      return null;
    }
  };

  const handleRestore = async (key: string, dropExisting: boolean, recoveryCode?: string): Promise<boolean> => {
    try {
      const result = await BackupAPI.restore(key, dropExisting, recoveryCode);
      if (result.success) {
        toast.success(getRestoreMessage(result));
        return true;
      }
      if (result.status === 'recovery_code_required') {
        toast(getRestoreMessage(result));
      } else {
        toast.error(getRestoreMessage(result));
      }
      return false;
    } catch (error) {
      console.error('Failed to restore backup:', error);
      if (error instanceof ApiError) {
        toast.error(error.status === 429 ? 'Слишком много попыток восстановления. Попробуйте чуть позже.' : error.message);
      } else if (error instanceof AxiosError) {
        toast.error(error.response?.data?.detail || error.message);
      } else if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error('Ошибка восстановления');
      }
      return false;
    }
  };

  const handleDelete = async (key: string) => {
    try {
      await BackupAPI.delete(key);
      toast.success('Бэкап удалён');
      setBackups((current) => current.filter((backup) => backup.key !== key));
    } catch (error) {
      console.error('Failed to delete backup:', error);
      toast.error('Ошибка удаления бэкапа');
    }
  };

  const handleUpload = async (file: File): Promise<boolean> => {
    try {
      const result = await BackupAPI.upload(file);
      if (!result.success) {
        toast.error(getUploadMessage(result));
        return false;
      }
      if (result.verification_status === 'recovery_code_required') {
        toast(getUploadMessage(result));
      } else {
        toast.success(getUploadMessage(result));
      }
      if (result.offsite_error) {
        toast(result.offsite_error);
      }
      await loadData();
      return true;
    } catch (error) {
      console.error('Failed to upload backup:', error);
      toast.error('Ошибка загрузки бэкапа');
      return false;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[180px] rounded-xl" />
        <Skeleton className="h-[300px] rounded-xl" />
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {health && (
        <Card className="border-border/50">
          <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {health.status === 'healthy' ? <ShieldCheck className="h-4 w-4 text-green-500" /> : <TriangleAlert className="h-4 w-4 text-amber-500" />}
                <p className="text-sm font-semibold text-foreground">Состояние backup/recovery</p>
              </div>
              <p className="text-sm text-muted-foreground">
                {health.checks?.backups?.latest ? `Последний бэкап: ${health.checks.backups.latest}` : 'Последний бэкап ещё не найден'}
              </p>
              {typeof health.checks?.backups?.age_hours === 'number' && (
                <p className="text-xs text-muted-foreground">
                  Возраст: {health.checks.backups.age_hours.toFixed(2)} ч
                  {typeof health.expected_max_age_hours === 'number' ? ` • лимит ${health.expected_max_age_hours.toFixed(0)} ч` : ''}
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={health.freshness_status === 'fresh' || health.freshness_status === 'disabled' ? 'default' : 'destructive'}>
                {health.freshness_status}
              </Badge>
              <Badge variant={health.offsite_configured ? 'outline' : 'secondary'}>
                {health.offsite_configured ? 'Offsite configured' : 'Offsite off'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {latestPortableBackup && (
        <Card className="border-amber-500/40 bg-amber-500/5">
          <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-foreground">Recovery code для {latestPortableBackup.backupKey}</p>
              <p className="text-sm text-muted-foreground">
                Сохраните его отдельно от файла. Сервер больше не покажет этот код и не хранит его для повторной выдачи.
              </p>
              <code className="block w-fit rounded-md bg-background px-3 py-2 text-sm font-medium">
                {latestPortableBackup.recoveryCode}
              </code>
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={handleCopyRecoveryCode}>
                <Copy className="mr-2 h-4 w-4" />
                Скопировать
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => setLatestPortableBackup(null)}>
                Скрыть
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <BackupSettingsCard settings={settings} isSaving={isSaving} onSave={handleSaveSettings} />
      <BackupListCard
        backups={backups}
        isLoading={isLoading}
        isCreating={isCreating}
        onRefresh={loadData}
        onCreate={handleCreateBackup}
        onVerify={handleVerify}
        onRestore={handleRestore}
        onDelete={handleDelete}
        onUpload={handleUpload}
      />
    </div>
  );
}
