import { api } from './client';
import type { Lab, LabCreate, LabUpdate } from './types';

export const LabsAPI = {
  // Student endpoints
  list: async () => {
    const { data } = await api.get<Lab[]>('/labs/');
    return data;
  },

  uploadSolution: async (labId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await api.post<{ status: string; submission_id: string }>(
      `/labs/${labId}/submit`, 
      formData, 
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return data;
  },

  // Admin endpoints
  adminList: async () => {
    const { data } = await api.get<Lab[]>('/admin/labs');
    return data;
  },

  adminGet: async (id: string) => {
    const { data } = await api.get<Lab>(`/admin/labs/${id}`);
    return data;
  },

  adminCreate: async (lab: LabCreate) => {
    const { data } = await api.post<Lab>('/admin/labs', lab);
    return data;
  },

  adminUpdate: async (id: string, lab: LabUpdate) => {
    const { data } = await api.patch<Lab>(`/admin/labs/${id}`, lab);
    return data;
  },

  adminDelete: async (id: string) => {
    const { data } = await api.delete<{ status: string }>(`/admin/labs/${id}`);
    return data;
  },

  adminPublish: async (id: string) => {
    const { data } = await api.post<{ status: string; public_code: string }>(`/admin/labs/${id}/publish`);
    return data;
  },

  adminUnpublish: async (id: string) => {
    const { data } = await api.post<{ status: string }>(`/admin/labs/${id}/unpublish`);
    return data;
  },
};
