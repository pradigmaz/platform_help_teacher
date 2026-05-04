import { api } from './client';
import type { Lab, LabCreate, LabUpdate, LabSettings } from './types';

// Типы для продлений дедлайнов
export interface DeadlineExtension {
  id: string;
  lab_id: string;
  group_id: string;
  bonus_lessons: number;
  reason: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  lab_number: number | null;
  lab_title: string | null;
  group_name: string | null;
  creator_name: string | null;
}

export interface DeadlineExtensionCreate {
  lab_id: string;
  group_id: string;
  bonus_lessons: number;
  reason?: string;
  expires_at?: string;
}

export interface DeadlineExtensionUpdate {
  bonus_lessons?: number;
  reason?: string;
  expires_at?: string;
  is_active?: boolean;
}

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
  getSettings: async () => {
    const { data } = await api.get<LabSettings>('/admin/lab-settings');
    return data;
  },

  adminList: async (subjectId?: string) => {
    const { data } = await api.get<Lab[]>('/admin/labs', {
      params: subjectId ? { subject_id: subjectId } : undefined,
    });
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

  // Deadline Extensions
  getExtensions: async (labId?: string, groupId?: string, isActive?: boolean) => {
    const params = new URLSearchParams();
    if (labId) params.append('lab_id', labId);
    if (groupId) params.append('group_id', groupId);
    if (isActive !== undefined) params.append('is_active', String(isActive));
    const { data } = await api.get<{ items: DeadlineExtension[]; total: number }>(
      `/admin/deadline-extensions?${params.toString()}`
    );
    return data;
  },

  createExtension: async (ext: DeadlineExtensionCreate) => {
    const { data } = await api.post<DeadlineExtension>('/admin/deadline-extensions', ext);
    return data;
  },

  updateExtension: async (id: string, ext: DeadlineExtensionUpdate) => {
    const { data } = await api.patch<DeadlineExtension>(`/admin/deadline-extensions/${id}`, ext);
    return data;
  },

  deleteExtension: async (id: string) => {
    const { data } = await api.delete<{ status: string }>(`/admin/deadline-extensions/${id}`);
    return data;
  },
};
