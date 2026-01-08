/**
 * API для работы с аудитом действий.
 */
import api from './client';

export interface SuspicionMatch {
  has_suspicion: boolean;
  fingerprint_match?: {
    user_id: string;
    user_name: string;
    match_count: number;
    match_type: string;
  };
  ip_match?: {
    user_id: string;
    user_name: string;
    match_count: number;
    match_type: string;
  };
  vpn_detected?: {
    detected: boolean;
    reason: string;
    timezone: string;
    language: string;
    expected_countries: string[];
  };
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  user_name: string | null;
  action_type: string;
  entity_type: string | null;
  entity_id: string | null;
  method: string;
  path: string;
  query_params?: Record<string, unknown>;
  request_body?: Record<string, unknown>;
  response_status: number | null;
  duration_ms: number | null;
  ip_address: string;
  ip_forwarded: string | null;
  user_agent: string | null;
  fingerprint?: Record<string, unknown>;
  extra_data?: Record<string, unknown>;
  created_at: string;
  suspicion?: SuspicionMatch;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}

export interface AuditStats {
  total_logs: number;
  unique_users: number;
  unique_ips: number;
  by_action_type: Record<string, number>;
  period_days: number;
}

export interface AuditFilters {
  user_id?: string;
  action_type?: string;
  ip_address?: string;
  date_from?: string;
  date_to?: string;
  path_contains?: string;
  skip?: number;
  limit?: number;
}

export const AuditAPI = {
  /**
   * Получить логи аудита с фильтрами.
   */
  async getLogs(filters: AuditFilters = {}): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.action_type) params.append('action_type', filters.action_type);
    if (filters.ip_address) params.append('ip_address', filters.ip_address);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.path_contains) params.append('path_contains', filters.path_contains);
    if (filters.skip !== undefined) params.append('skip', String(filters.skip));
    if (filters.limit !== undefined) params.append('limit', String(filters.limit));
    
    const { data } = await api.get<AuditLogListResponse>(`/admin/audit?${params}`);
    return data;
  },

  /**
   * Получить детали записи аудита.
   */
  async getLogDetail(logId: string): Promise<AuditLog> {
    const { data } = await api.get<AuditLog>(`/admin/audit/${logId}`);
    return data;
  },

  /**
   * Получить логи конкретного пользователя.
   */
  async getUserLogs(userId: string, skip = 0, limit = 50): Promise<AuditLogListResponse> {
    const { data } = await api.get<AuditLogListResponse>(
      `/admin/audit/user/${userId}?skip=${skip}&limit=${limit}`
    );
    return data;
  },

  /**
   * Получить статистику аудита.
   */
  async getStats(days = 7): Promise<AuditStats> {
    const { data } = await api.get<AuditStats>(`/admin/audit/stats/summary?days=${days}`);
    return data;
  },

  /**
   * Экспорт логов в JSONL для анализа ИИ.
   */
  async exportLogs(filters: {
    user_id?: string;
    action_type?: string;
    date_from?: string;
    date_to?: string;
    days?: number;
    limit?: number;
  } = {}): Promise<void> {
    const params = new URLSearchParams();
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.action_type) params.append('action_type', filters.action_type);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.days !== undefined) params.append('days', String(filters.days));
    if (filters.limit !== undefined) params.append('limit', String(filters.limit));
    
    const response = await api.get(`/admin/audit/export?${params}`, {
      responseType: 'blob',
    });
    
    // Скачиваем файл
    const blob = new Blob([response.data], { type: 'application/x-ndjson' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_${new Date().toISOString().slice(0, 10)}.jsonl`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },

  /**
   * Экспорт логов конкретного пользователя.
   */
  async exportUserLogs(userId: string, days = 30): Promise<void> {
    const response = await api.get(`/admin/audit/export/user/${userId}?days=${days}`, {
      responseType: 'blob',
    });
    
    const blob = new Blob([response.data], { type: 'application/x-ndjson' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_user_${userId}_${new Date().toISOString().slice(0, 10)}.jsonl`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },
};
