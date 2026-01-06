import { api } from './client';
import type {
  TeacherContactsData,
  TeacherContactsUpdate,
  RelinkTelegramResponse,
} from './types';

export const AdminAPI = {
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
};
