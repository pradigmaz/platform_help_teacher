import { api } from './client';

export type BackupVerificationStatus =
  | 'valid'
  | 'recovery_code_required'
  | 'invalid_recovery_code'
  | 'file_corrupted'
  | 'archive_corrupted'
  | 'dump_invalid'
  | 'decryption_failed'
  | 'download_failed'
  | 'unsupported_format'
  | 'unknown_error'
  | string;

export interface BackupInfo {
  name: string;
  key: string;
  size: number;
  created_at: string;
  format_version?: number | null;
  portable?: boolean | null;
  key_fingerprint?: string | null;
  created_with_current_key?: boolean | null;
  offsite_present?: boolean | null;
}

export interface BackupListResponse {
  backups: BackupInfo[];
  total: number;
}

export interface BackupCreateResponse {
  success: boolean;
  backup_key?: string;
  recovery_code?: string | null;
  format_version?: number | null;
  portable?: boolean | null;
  key_fingerprint?: string | null;
  created_with_current_key?: boolean | null;
  mirrored_offsite?: boolean | null;
  offsite_error?: string | null;
  size?: number;
  uploaded?: boolean;
  notification_sent?: boolean | null;
  notification_error?: string | null;
  error?: string;
}

export interface UploadBackupResponse {
  success: boolean;
  backup_key?: string;
  size?: number;
  verified?: boolean;
  verification_status?: BackupVerificationStatus | null;
  format_version?: number | null;
  portable?: boolean | null;
  created_with_current_key?: boolean | null;
  mirrored_offsite?: boolean | null;
  offsite_error?: string | null;
  error?: string;
}

export interface BackupSettings {
  enabled: boolean;
  schedule_hour: number;
  schedule_minute: number;
  retention_days: number;
  max_backups: number;
  notify_on_success: boolean;
  notify_on_failure: boolean;
}

export interface BackupSettingsUpdate {
  enabled?: boolean;
  schedule_hour?: number;
  schedule_minute?: number;
  retention_days?: number;
  max_backups?: number;
  notify_on_success?: boolean;
  notify_on_failure?: boolean;
}

export interface RestoreResponse {
  success: boolean;
  status?: BackupVerificationStatus;
  format_version?: number | null;
  portable?: boolean | null;
  created_with_current_key?: boolean | null;
  offsite_used?: boolean | null;
  error?: string;
}

export interface VerifyResponse {
  valid: boolean;
  backup_key: string;
  status?: BackupVerificationStatus;
  format_version?: number | null;
  portable?: boolean | null;
  created_with_current_key?: boolean | null;
  offsite_used?: boolean | null;
  error?: string | null;
}

export interface BackupHealthCheck {
  status: string;
  message?: string;
  count?: number;
  latest?: string | null;
  age_hours?: number | null;
  latest_created_at?: string | null;
}

export interface BackupHealthResponse {
  status: string;
  freshness_status: string;
  expected_max_age_hours?: number | null;
  offsite_configured: boolean;
  checks?: Record<string, BackupHealthCheck>;
}

export interface BotStatusResponse {
  telegram_available: boolean;
  vk_available: boolean;
  telegram_admin_id: number | null;
  vk_admin_id: number | null;
}

export const BackupAPI = {
  getSettings: async () => (await api.get<BackupSettings>('/admin/backups/settings')).data,
  updateSettings: async (data: BackupSettingsUpdate) => (await api.put<BackupSettings>('/admin/backups/settings', data)).data,

  list: async () => (await api.get<BackupListResponse>('/admin/backups/')).data,
  create: async (name?: string) => (await api.post<BackupCreateResponse>('/admin/backups', name ? { name } : {})).data,
  verify: async (key: string, recoveryCode?: string) =>
    (
      await api.post<VerifyResponse>(`/admin/backups/${encodeURIComponent(key)}/verify`, {
        recovery_code: recoveryCode?.trim() || undefined,
      })
    ).data,
  restore: async (key: string, dropExisting = false, recoveryCode?: string) =>
    (
      await api.post<RestoreResponse>(`/admin/backups/${encodeURIComponent(key)}/restore`, {
        drop_existing: dropExisting,
        recovery_code: recoveryCode?.trim() || undefined,
        confirmation: `RESTORE-${key}`,
      })
    ).data,
  delete: async (key: string) => (await api.delete(`/admin/backups/${encodeURIComponent(key)}`)).data,

  upload: async (file: File, recoveryCode?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (recoveryCode?.trim()) {
      formData.append('recovery_code', recoveryCode.trim());
    }
    return (
      await api.post<UploadBackupResponse>('/admin/backups/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },

  health: async () => (await api.get<BackupHealthResponse>('/admin/backups/health')).data,
  getBotStatus: async () => (await api.get<BotStatusResponse>('/admin/backups/bot-status')).data,
};
