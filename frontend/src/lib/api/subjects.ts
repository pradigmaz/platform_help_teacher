import { api } from './client';
import type { AutomaticQueueResponse, FinalControlType, GroupSubjectOffering, OfferingPolicy } from './types';

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

  getOfferingPolicy: async (offeringId: string) => {
    const { data } = await api.get<OfferingPolicy>(`/admin/subjects/offerings/${offeringId}/policy`);
    return data;
  },

  updateOfferingPolicy: async (offeringId: string, policy: Omit<OfferingPolicy, 'offering_id' | 'source' | 'second_extra_required' | 'automatic_extra_required'>) => {
    const { data } = await api.put<OfferingPolicy>(`/admin/subjects/offerings/${offeringId}/policy`, policy);
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
