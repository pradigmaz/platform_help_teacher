import { api } from './client';

export interface DeviceInfo {
  platform: string | null;
  browser: string | null;
  screen: string | null;
}

export interface Session {
  session_id: string;
  created_at: string;
  ip_address: string | null;
  device: DeviceInfo;
  is_current: boolean;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
  max_sessions: number;
}

export interface RevokeSessionsResponse {
  revoked_count: number;
  message: string;
}

export const SessionsAPI = {
  getSessions: async (): Promise<SessionListResponse> => {
    const { data } = await api.get<SessionListResponse>('/users/me/sessions');
    return data;
  },

  revokeSession: async (sessionId: string): Promise<RevokeSessionsResponse> => {
    const { data } = await api.delete<RevokeSessionsResponse>(`/users/me/sessions/${sessionId}`);
    return data;
  },

  revokeAllSessions: async (): Promise<RevokeSessionsResponse> => {
    const { data } = await api.post<RevokeSessionsResponse>('/users/me/sessions/revoke-all');
    return data;
  },
};
