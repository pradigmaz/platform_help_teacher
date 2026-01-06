import { api } from './client';
import type { Lab } from './types';

export const LabsAPI = {
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
};
