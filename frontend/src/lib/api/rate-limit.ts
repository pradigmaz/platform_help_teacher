/**
 * API для управления rate limit банами.
 */
import api from './client';

export interface RateLimitWarning {
  id: string;
  user_id: string | null;
  user_name: string | null;
  ip_address: string;
  warning_level: string;
  violation_count: number;
  message: string | null;
  ban_until: string | null;
  unbanned_at: string | null;
  admin_notified: boolean;
  created_at: string;
}

export interface WarningListResponse {
  items: RateLimitWarning[];
  total: number;
}

export interface UnbanResponse {
  success: boolean;
  message: string;
  warning_id: string;
}

export const RateLimitAPI = {
  /**
   * Получить активные баны.
   */
  async getActiveBans(skip = 0, limit = 50): Promise<WarningListResponse> {
    const { data } = await api.get<WarningListResponse>(
      `/admin/rate-limits/bans?skip=${skip}&limit=${limit}`
    );
    return data;
  },

  /**
   * Получить историю предупреждений.
   */
  async getHistory(params: {
    user_id?: string;
    ip_address?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<WarningListResponse> {
    const searchParams = new URLSearchParams();
    if (params.user_id) searchParams.append('user_id', params.user_id);
    if (params.ip_address) searchParams.append('ip_address', params.ip_address);
    if (params.skip !== undefined) searchParams.append('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.append('limit', String(params.limit));
    
    const { data } = await api.get<WarningListResponse>(
      `/admin/rate-limits/history?${searchParams}`
    );
    return data;
  },

  /**
   * Разбанить по ID предупреждения.
   */
  async unban(warningId: string, reason: string): Promise<UnbanResponse> {
    const { data } = await api.post<UnbanResponse>(
      `/admin/rate-limits/unban/${warningId}`,
      { reason }
    );
    return data;
  },

  /**
   * Разбанить все баны пользователя.
   */
  async unbanUser(userId: string, reason: string): Promise<UnbanResponse> {
    const { data } = await api.post<UnbanResponse>(
      `/admin/rate-limits/unban/user/${userId}`,
      { reason }
    );
    return data;
  },
};
