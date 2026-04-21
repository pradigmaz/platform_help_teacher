import { api } from './client';
import type {
  AdminExamOfferingContext,
  AdminExamQuestionBankDetail,
  AdminExamSubjectGroup,
  ExamPrepQuestion,
} from './types';

export const ExamBanksAPI = {
  listGroups: async (semester?: string) => {
    const { data } = await api.get<AdminExamSubjectGroup[]>('/admin/exams/groups', {
      params: semester ? { semester } : undefined,
    });
    return data;
  },

  getBank: async (bankId: string) => {
    const { data } = await api.get<AdminExamQuestionBankDetail>(`/admin/exams/banks/${bankId}`);
    return data;
  },

  createBank: async (offeringIds: string[], questions: ExamPrepQuestion[] = []) => {
    const { data } = await api.post<AdminExamQuestionBankDetail>('/admin/exams/banks', {
      offering_ids: offeringIds,
      questions,
    });
    return data;
  },

  updateBank: async (bankId: string, questions: ExamPrepQuestion[]) => {
    const { data } = await api.put<AdminExamQuestionBankDetail>(`/admin/exams/banks/${bankId}`, {
      questions,
    });
    return data;
  },

  assignBank: async (bankId: string, offeringIds: string[]) => {
    const { data } = await api.post<AdminExamQuestionBankDetail>(`/admin/exams/banks/${bankId}/assign`, {
      offering_ids: offeringIds,
    });
    return data;
  },

  splitBank: async (bankId: string, offeringIds: string[]) => {
    const { data } = await api.post<AdminExamQuestionBankDetail>(`/admin/exams/banks/${bankId}/split`, {
      offering_ids: offeringIds,
    });
    return data;
  },

  getOfferingContext: async (offeringId: string) => {
    const { data } = await api.get<AdminExamOfferingContext>(`/admin/exams/offerings/${offeringId}/context`);
    return data;
  },
};
