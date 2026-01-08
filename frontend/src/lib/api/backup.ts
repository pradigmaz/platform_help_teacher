import { api } from './client';

export interface BackupInfo {
  name: string;
  key: string;
  size: number;
  created_at: string;
}

export interface BackupListResponse {
  backups: BackupInfo[];
  total: number;
}

export interface BackupCreateResponse {
  success: boolean;
  backup_key?: string;
  size?: number;
  error?: string;
}

export interface BackupSettings {
  enabled: boolean;
  schedule_hour: number;
  schedule_minute: number;
  retention_days: number;
  max_backups: number;
  storage_bucket: string;
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
  error?: string;
}

export interface VerifyResponse {
  valid: boolean;
  backup_key: string;
}

export const BackupAPI = {
  // Settings
  getSettings: () => api.get<BackupSettings>('/admin/backups/settings'),
  updateSettings: (data: BackupSettingsUpdate) => 
    api.put<BackupSettings>('/admin/backups/settings', data),

  // Backups
  list: () => api.get<BackupListResponse>('/admin/backups'),
  create: (name?: string) => 
    api.post<BackupCreateResponse>('/admin/backups', name ? { name } : {}),
  verify: (key: string) => 
    api.post<VerifyResponse>(`/admin/backups/${encodeURIComponent(key)}/verify`),
  restore: (key: string, dropExisting: boolean = false) => 
    api.post<RestoreResponse>(`/admin/backups/${encodeURIComponent(key)}/restore`, { 
      drop_existing: dropExisting,
      confirmation: `RESTORE-${key}`
    }),
  delete: (key: string) => 
    api.delete(`/admin/backups/${encodeURIComponent(key)}`),
};
