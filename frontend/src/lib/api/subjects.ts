import { api } from './client';
import type { AdminExamPrepResponse, AutomaticQueueResponse, FinalControlType, GroupSubjectOffering, ExamPrepQuestion } from './types';

export const SubjectsAPI = {
  listOfferings: async (semester?: string) => {
    const { data } = await api.get<GroupSubjectOffering[]>('/admin/subjects/offerings', {
      params: semester ? { semester } : undefined,
    });
    return data;
  },

  updateOffering: async (offeringId: string, finalControlType: FinalControlType | null) => {
    const { data } = await api.patch<GroupSubjectOffering>(`/admin/subjects/offerings/${offeringId}`, {
      final_control_type: finalControlType,
    });
    return data;
  },

  getAutomaticQueue: async (offeringId: string) => {
    const { data } = await api.get<AutomaticQueueResponse>(`/admin/subjects/offerings/${offeringId}/automatic-queue`);
    return data;
  },

  getExamPrep: async (offeringId: string) => {
    const { data } = await api.get<AdminExamPrepResponse>(`/admin/subjects/offerings/${offeringId}/exam-prep`);
    return data;
  },

  updateExamPrep: async (offeringId: string, questions: ExamPrepQuestion[]) => {
    const { data } = await api.put<AdminExamPrepResponse>(
      `/admin/subjects/offerings/${offeringId}/exam-prep`,
      { questions },
    );
    return data;
  },

  declineAutomatic: async (offeringId: string, studentId: string, reason?: string) => {
    const { data } = await api.post<AutomaticQueueResponse>(
      `/admin/subjects/offerings/${offeringId}/automatic-refusals/${studentId}`,
      { reason: reason?.trim() || null },
    );
    return data;
  },

  clearAutomaticDecline: async (offeringId: string, studentId: string) => {
    const { data } = await api.delete<AutomaticQueueResponse>(
      `/admin/subjects/offerings/${offeringId}/automatic-refusals/${studentId}`,
    );
    return data;
  },
};
