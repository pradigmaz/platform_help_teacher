'use client';

import { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { toast } from 'sonner';
import {
  ApiError,
  BackupAPI,
  type BackupHealthResponse,
  type BackupInfo,
  type BackupSettings,
  type BackupSettingsUpdate,
  type VerifyResponse,
} from '@/lib/api';
import {
  getCreateMessage,
  getRestoreMessage,
  getUploadMessage,
  getVerifyMessage,
} from './backupTabMessages';

const DEFAULT_SETTINGS: BackupSettings = {
  enabled: true,
  schedule_hour: 17,
  schedule_minute: 0,
  retention_days: 30,
  max_backups: 10,
  notify_on_success: false,
  notify_on_failure: true,
};

export function useBackupTab() {
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

  const handleSaveSettings = useCallback(async (data: BackupSettingsUpdate) => {
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
  }, []);

  const handleCreateBackup = useCallback(async () => {
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
  }, [loadData]);

  const handleVerify = useCallback(async (key: string, recoveryCode?: string): Promise<VerifyResponse | null> => {
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
  }, []);

  const handleRestore = useCallback(async (key: string, dropExisting: boolean, recoveryCode?: string): Promise<boolean> => {
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
  }, []);

  const handleDelete = useCallback(async (key: string) => {
    try {
      await BackupAPI.delete(key);
      toast.success('Бэкап удалён');
      setBackups((current) => current.filter((backup) => backup.key !== key));
    } catch (error) {
      console.error('Failed to delete backup:', error);
      toast.error('Ошибка удаления бэкапа');
    }
  }, []);

  const handleUpload = useCallback(async (file: File): Promise<boolean> => {
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
  }, [loadData]);

  return {
    latestPortableBackup,
    setLatestPortableBackup,
    isLoading,
    isSaving,
    isCreating,
    settings,
    backups,
    health,
    handleCopyRecoveryCode,
    loadData,
    handleSaveSettings,
    handleCreateBackup,
    handleVerify,
    handleRestore,
    handleDelete,
    handleUpload,
  };
}
