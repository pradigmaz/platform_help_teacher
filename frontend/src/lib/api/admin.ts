import { api } from './client';
import { buildAuthFingerprintHeaders } from './fingerprint-auth';
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

export const AdminAPI = {
  getProfile: async (): Promise<AdminProfile> => {
    const { data } = await api.get<AdminProfile>('/users/me');
    return data;
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
