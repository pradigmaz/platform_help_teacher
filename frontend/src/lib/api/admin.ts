import { api } from './client';
import { buildAuthFingerprintHeaders } from './fingerprint-auth';
import { clearSingleFlight, runSingleFlight } from '../single-flight';
import type {
  TeacherContactsData,
  TeacherContactsUpdate,
  RelinkTelegramResponse,
  LinkVkResponse,
} from './types';

export interface AdminProfile {
  id: string;
  full_name: string;
  username?: string;
  telegram_id?: number;
  vk_id?: number;
  role: 'admin' | 'teacher' | 'student';
  onboarding_completed: boolean;
}

export interface AdminStats {
  total_users: number;
  total_students: number;
  total_groups: number;
  total_lectures?: number;
  active_labs: number;
}

export const AdminAPI = {
  getProfile: async (): Promise<AdminProfile> => {
    const { data } = await api.get<AdminProfile>('/users/me');
    return data;
  },

  getStats: async (options?: { force?: boolean }): Promise<AdminStats> => {
    const key = 'admin:stats';
    if (options?.force) {
      clearSingleFlight(key);
    }

    return runSingleFlight(key, async () => {
      const { data } = await api.get<AdminStats>('/admin/stats');
      return data;
    });
  },

  getContacts: async (): Promise<TeacherContactsData> => {
    const { data } = await api.get<TeacherContactsData>('/users/profile/contacts');
    return data;
  },

  updateContacts: async (payload: TeacherContactsUpdate): Promise<TeacherContactsData> => {
    const { data } = await api.put<TeacherContactsData>('/users/profile/contacts', payload);
    return data;
  },

  relinkTelegram: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/relink-telegram');
    return data;
  },

  linkVk: async (): Promise<LinkVkResponse> => {
    const { data } = await api.post<LinkVkResponse>('/users/me/link-vk');
    return data;
  },

  impersonateUser: async (userId: string): Promise<void> => {
    await api.post(`/admin/impersonate/${userId}`, undefined, {
      headers: buildAuthFingerprintHeaders(),
    });
  },

  exitImpersonation: async (): Promise<void> => {
    await api.post('/admin/impersonate/exit', undefined, {
      headers: buildAuthFingerprintHeaders(),
    });
  },
};
