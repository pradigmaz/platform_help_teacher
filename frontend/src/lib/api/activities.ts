import { api } from './client';
import type {
  AttestationType,
  ActivityCreate,
  ActivityUpdate,
  ActivityResponse,
  ActivityWithStudentResponse,
} from './types';

export const ActivitiesAPI = {
  create: async (payload: ActivityCreate) => {
    const { data } = await api.post<ActivityResponse[]>('/admin/activities', payload);
    return data;
  },

  getAll: async (attestationType?: AttestationType, limit = 100) => {
    const params = new URLSearchParams();
    if (attestationType) params.append('attestation_type', attestationType);
    params.append('limit', limit.toString());
    const { data } = await api.get<ActivityWithStudentResponse[]>(`/admin/activities?${params}`);
    return data;
  },

  getByStudent: async (studentId: string) => {
    const { data } = await api.get<ActivityResponse[]>(`/admin/activities/student/${studentId}`);
    return data;
  },

  update: async (id: string, payload: ActivityUpdate) => {
    const { data } = await api.patch<ActivityResponse>(`/admin/activities/${id}`, payload);
    return data;
  },

  delete: async (id: string) => {
    const { data } = await api.delete<ActivityResponse>(`/admin/activities/${id}`);
    return data;
  },
};
