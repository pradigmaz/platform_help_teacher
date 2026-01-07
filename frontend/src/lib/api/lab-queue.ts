import { api } from './client';
import type { LabQueue, SubmissionDetail, AcceptSubmissionRequest, RejectSubmissionRequest } from './types/lab-queue';

export const LabQueueAPI = {
  getQueue: async (subjectId?: string) => {
    const { data } = await api.get<LabQueue[]>('/admin/labs/queue', {
      params: subjectId ? { subject_id: subjectId } : undefined,
    });
    return data;
  },

  getSubmissionDetail: async (submissionId: string) => {
    const { data } = await api.get<SubmissionDetail>(`/admin/labs/submissions/${submissionId}`);
    return data;
  },

  acceptSubmission: async (submissionId: string, request: AcceptSubmissionRequest) => {
    const { data } = await api.post<{ status: string; submission_id: string; grade: number; lesson_grade_synced: boolean }>(
      `/admin/labs/submissions/${submissionId}/accept`,
      request
    );
    return data;
  },

  rejectSubmission: async (submissionId: string, request: RejectSubmissionRequest) => {
    const { data } = await api.post<{ status: string; submission_id: string; comment: string }>(
      `/admin/labs/submissions/${submissionId}/reject`,
      request
    );
    return data;
  },
};
