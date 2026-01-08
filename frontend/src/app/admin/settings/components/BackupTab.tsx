'use client';

import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { BackupAPI, type BackupInfo, type BackupSettings, type BackupSettingsUpdate } from '@/lib/api';
import { BackupSettingsCard } from './BackupSettingsCard';
import { BackupListCard } from './BackupListCard';
import { Skeleton } from '@/components/ui/skeleton';

const DEFAULT_SETTINGS: BackupSettings = {
  enabled: true,
  schedule_hour: 17,
  schedule_minute: 0,
  retention_days: 30,
  max_backups: 10,
  storage_bucket: 'edu-backups',
  notify_on_success: false,
  notify_on_failure: true,
};

export function BackupTab() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [settings, setSettings] = useState<BackupSettings>(DEFAULT_SETTINGS);
  const [backups, setBackups] = useState<BackupInfo[]>([]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [settingsData, backupsData] = await Promise.all([
        BackupAPI.getSettings(),
        BackupAPI.list(),
      ]);
      setSettings(settingsData);
      setBackups(backupsData?.backups || []);
    } catch (error) {
      console.error('Failed to load backup data:', error);
      toast.error('Ошибка загрузки данных бэкапов');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
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
      if (result.success) {
        toast.success(`Бэкап создан: ${result.backup_key}`);
        await loadData();
      } else {
        toast.error(`Ошибка: ${result.error}`);
      }
    } catch (error) {
      console.error('Failed to create backup:', error);
      toast.error('Ошибка создания бэкапа');
    } finally {
      setIsCreating(false);
    }
  };

  const handleVerify = async (key: string): Promise<boolean> => {
    try {
      const result = await BackupAPI.verify(key);
      if (result.valid) {
        toast.success('Бэкап валиден');
      } else {
        toast.error('Бэкап повреждён');
      }
      return result.valid;
    } catch (error) {
      console.error('Failed to verify backup:', error);
      toast.error('Ошибка проверки бэкапа');
      return false;
    }
  };

  const handleRestore = async (key: string, dropExisting: boolean): Promise<boolean> => {
    try {
      const result = await BackupAPI.restore(key, dropExisting);
      if (result.success) {
        toast.success('База данных восстановлена');
        return true;
      } else {
        toast.error(`Ошибка: ${result.error}`);
        return false;
      }
    } catch (error) {
      console.error('Failed to restore backup:', error);
      toast.error('Ошибка восстановления');
      return false;
    }
  };

  const handleDelete = async (key: string) => {
    try {
      await BackupAPI.delete(key);
      toast.success('Бэкап удалён');
      setBackups(backups.filter(b => b.key !== key));
    } catch (error) {
      console.error('Failed to delete backup:', error);
      toast.error('Ошибка удаления бэкапа');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[300px] rounded-xl" />
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BackupSettingsCard
        settings={settings}
        isSaving={isSaving}
        onSave={handleSaveSettings}
      />
      <BackupListCard
        backups={backups}
        isLoading={isLoading}
        isCreating={isCreating}
        onRefresh={loadData}
        onCreate={handleCreateBackup}
        onVerify={handleVerify}
        onRestore={handleRestore}
        onDelete={handleDelete}
      />
    </div>
  );
}
