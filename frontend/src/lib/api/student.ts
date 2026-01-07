import { api } from './client';
import type {
  StudentProfile,
  StudentAttendance,
  StudentLab,
  StudentLabDetail,
  StudentAttestation,
  StudentTeacherContacts,
  RelinkTelegramResponse,
} from './types';

export const StudentAPI = {
  getProfile: async () => {
    const { data } = await api.get<StudentProfile>('/student/profile');
    return data;
  },

  getAttendance: async () => {
    const { data } = await api.get<StudentAttendance>('/student/attendance');
    return data;
  },

  getLabs: async () => {
    const { data } = await api.get<StudentLab[]>('/student/labs');
    return data;
  },

  getLabDetail: async (labId: string) => {
    const { data } = await api.get<StudentLabDetail>(`/student/labs/${labId}`);
    return data;
  },

  markLabReady: async (labId: string) => {
    const { data } = await api.post<{ status: string; submission_id: string; variant_number?: number; message: string }>(`/student/labs/${labId}/ready`);
    return data;
  },

  cancelLabReady: async (labId: string) => {
    const { data } = await api.post<{ status: string; message: string }>(`/student/labs/${labId}/cancel-ready`);
    return data;
  },

  getAttestation: async (type: 'first' | 'second') => {
    const { data } = await api.get<StudentAttestation>(`/student/attestation/${type}`);
    return data;
  },

  getTeacherContacts: async (): Promise<StudentTeacherContacts> => {
    const { data } = await api.get<StudentTeacherContacts>('/student/teacher/contacts');
    return data;
  },

  relinkTelegram: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/relink-telegram');
    return data;
  },

  linkVk: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/link-vk');
    return data;
  },
};
