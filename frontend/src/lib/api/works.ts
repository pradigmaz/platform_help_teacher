import { api } from './client';
import type {
  WorkType,
  WorkCreate,
  WorkUpdate,
  WorkResponse,
  WorkSubmissionCreate,
  WorkSubmissionResponse,
} from './types';

export const WorksAPI = {
  create: async (workType: WorkType, data: WorkCreate) => {
    const { data: response } = await api.post<WorkResponse>(
      '/admin/works',
      { work_type: workType, ...data }
    );
    return response;
  },

  getByType: async (workType: WorkType) => {
    const { data } = await api.get<WorkResponse[]>(`/admin/works/${workType}`);
    return data;
  },

  update: async (workId: string, data: WorkUpdate) => {
    const { data: response } = await api.patch<WorkResponse>(
      `/admin/works/${workId}`,
      data
    );
    return response;
  },

  delete: async (workId: string) => {
    await api.delete(`/admin/works/${workId}`);
  },
};

export const WorkSubmissionsAPI = {
  submit: async (data: WorkSubmissionCreate) => {
    const { data: response } = await api.post<WorkSubmissionResponse>(
      '/admin/work-submissions',
      data
    );
    return response;
  },

  getByStudent: async (studentId: string, workType?: WorkType) => {
    const params = workType ? { work_type: workType } : {};
    const { data } = await api.get<WorkSubmissionResponse[]>(
      `/admin/work-submissions/student/${studentId}`,
      { params }
    );
    return data;
  },

  updateGrade: async (submissionId: string, grade: number, feedback?: string) => {
    const { data } = await api.patch<WorkSubmissionResponse>(
      `/admin/work-submissions/${submissionId}/grade`,
      { grade, feedback }
    );
    return data;
  },

  delete: async (submissionId: string) => {
    await api.delete(`/admin/work-submissions/${submissionId}`);
  },
};
