import { api } from './client';
import type { GroupResponse, GroupDetailResponse, GroupCreate, StudentImport } from './types';

export const GroupsAPI = {
  list: async () => {
    const { data } = await api.get<GroupResponse[]>('/groups/');
    return data;
  },

  get: async (id: string) => {
    const { data } = await api.get<GroupDetailResponse>(`/groups/${id}`);
    return data;
  },

  parseFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<StudentImport[]>('/groups/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  create: async (payload: GroupCreate) => {
    const { data } = await api.post<GroupResponse>('/groups/', payload);
    return data;
  },

  delete: async (id: string) => {
    await api.delete(`/groups/${id}`);
  },

  removeStudent: async (groupId: string, studentId: string) => {
    await api.delete(`/groups/${groupId}/students/${studentId}`);
  },

  addStudent: async (groupId: string, student: { full_name: string; username?: string }) => {
    const { data } = await api.post(`/groups/${groupId}/students`, student);
    return data;
  },

  generateCodes: async (groupId: string) => {
    const { data } = await api.post<{ generated: number; total_students: number }>(
      `/groups/${groupId}/generate-codes`
    );
    return data;
  },

  regenerateUserCode: async (userId: string) => {
    const { data } = await api.post<{ invite_code: string }>(
      `/groups/users/${userId}/regenerate-code`
    );
    return data;
  },

  regenerateGroupInviteCode: async (groupId: string) => {
    const { data } = await api.post<{ invite_code: string }>(
      `/groups/${groupId}/regenerate-invite-code`
    );
    return data;
  },

  assignSubgroup: async (groupId: string, subgroup: number | null, names: string[]) => {
    const { data } = await api.post<{
      matched: number;
      updated_students: string[];
      not_found: string[];
    }>(`/groups/${groupId}/assign-subgroup`, { subgroup, names });
    return data;
  },

  clearSubgroups: async (groupId: string) => {
    const { data } = await api.post<{ status: string; cleared: number }>(
      `/groups/${groupId}/clear-subgroups`
    );
    return data;
  },

  updateStudent: async (groupId: string, studentId: string, data: { full_name?: string; subgroup?: number | null }) => {
    const { data: result } = await api.patch(`/groups/${groupId}/students/${studentId}`, data);
    return result;
  },
};
