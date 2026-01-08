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
  getSettings: async () => (await api.get<BackupSettings>('/admin/backups/settings')).data,
  updateSettings: async (data: BackupSettingsUpdate) => 
    (await api.put<BackupSettings>('/admin/backups/settings', data)).data,

  // Backups
  list: async () => (await api.get<BackupListResponse>('/admin/backups')).data,
  create: async (name?: string) => 
    (await api.post<BackupCreateResponse>('/admin/backups', name ? { name } : {})).data,
  verify: async (key: string) => 
    (await api.post<VerifyResponse>(`/admin/backups/${encodeURIComponent(key)}/verify`)).data,
  restore: async (key: string, dropExisting: boolean = false) => 
    (await api.post<RestoreResponse>(`/admin/backups/${encodeURIComponent(key)}/restore`, { 
      drop_existing: dropExisting,
      confirmation: `RESTORE-${key}`
    })).data,
  delete: async (key: string) => 
    (await api.delete(`/admin/backups/${encodeURIComponent(key)}`)).data,
};
