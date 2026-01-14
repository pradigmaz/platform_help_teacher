/**
 * API для управления системой безопасности (детекция атак).
 */
import api from './client';

export interface StrikeDetail {
  timestamp: string;
  url: string;
  attack_type: string;
  description: string;
  severity: number;
}

export interface SecurityStrikesResponse {
  identifier: string;
  strike_count: number;
  is_banned: boolean;
  ban_ttl: number | null;
  strikes: StrikeDetail[];
}

export interface SecurityStatsResponse {
  total_bans: number;
  active_bans: number;
  strikes_today: number;
  top_attack_types: Record<string, number>;
}

export interface ClearStrikesResponse {
  success: boolean;
  identifier: string;
  message: string;
}

export interface UserInfoResponse {
  user_id: string;
  full_name: string;
  group_name: string | null;
  username: string | null;
  telegram_id: number | null;
}

export const SecurityAPI = {
  /**
   * Получить страйки по идентификатору.
   */
  async getStrikes(identifier: string): Promise<SecurityStrikesResponse> {
    const { data } = await api.get<SecurityStrikesResponse>(
      `/admin/security/strikes/${encodeURIComponent(identifier)}`
    );
    return data;
  },

  /**
   * Получить список активных банов за атаки.
   */
  async getActiveBans(skip = 0, limit = 50): Promise<SecurityStrikesResponse[]> {
    const { data } = await api.get<SecurityStrikesResponse[]>(
      `/admin/security/bans?skip=${skip}&limit=${limit}`
    );
    return data;
  },

  /**
   * Получить статистику безопасности.
   */
  async getStats(): Promise<SecurityStatsResponse> {
    const { data } = await api.get<SecurityStatsResponse>('/admin/security/stats');
    return data;
  },

  /**
   * Очистить страйки и снять бан.
   */
  async clearStrikes(identifier: string, reason?: string): Promise<ClearStrikesResponse> {
    const { data } = await api.delete<ClearStrikesResponse>('/admin/security/strikes', {
      data: { identifier, reason },
    });
    return data;
  },

  /**
   * Получить информацию о пользователе по UUID.
   */
  async getUserInfo(userId: string): Promise<UserInfoResponse> {
    const { data } = await api.get<UserInfoResponse>(`/admin/security/user/${userId}`);
    return data;
  },
};
