import { api, publicApi } from './client';
import { runSingleFlight } from '../single-flight';
import type {
  ReportCreate,
  ReportUpdate,
  Report,
  ReportListResponse,
  ReportViewsResponse,
  PublicReportData,
  PinVerifyResponse,
  StudentDetailData,
} from './types';

type ReportListParams = {
  groupId?: string;
  includeInactive?: boolean;
};

export const ReportsAPI = {
  create: async (payload: ReportCreate) => {
    const { data } = await api.post<Report>('/admin/reports', payload);
    return data;
  },

  list: async (params: ReportListParams = {}) => {
    const groupId = params.groupId ?? 'all';
    const includeInactive = params.includeInactive ?? false;
    return runSingleFlight(`reports:list:${groupId}:inactive:${includeInactive}`, async () => {
      const { data } = await api.get<ReportListResponse>('/admin/reports', {
        params: {
          group_id: params.groupId,
          include_inactive: includeInactive,
        },
      });
      return data;
    });
  },

  get: async (id: string) => {
    const { data } = await api.get<Report>(`/admin/reports/${id}`);
    return data;
  },

  update: async (id: string, payload: ReportUpdate) => {
    const { data } = await api.put<Report>(`/admin/reports/${id}`, payload);
    return data;
  },

  delete: async (id: string) => {
    await api.delete(`/admin/reports/${id}`);
  },

  regenerate: async (id: string) => {
    const { data } = await api.post<Report>(`/admin/reports/${id}/regenerate`);
    return data;
  },

  getViews: async (id: string) => {
    const { data } = await api.get<ReportViewsResponse>(`/admin/reports/${id}/views`);
    return data;
  },
};

export const PublicReportAPI = {
  getReport: async (code: string, attestation: 'first' | 'second' = 'first', signal?: AbortSignal) => {
    const { data } = await publicApi.get<PublicReportData>(
      `/public/report/${code}?attestation=${attestation}`,
      { signal }
    );
    return data;
  },

  verifyPin: async (code: string, pin: string) => {
    const { data } = await publicApi.post<PinVerifyResponse>(
      `/public/report/${code}/verify-pin`,
      { pin }
    );
    return data;
  },

  getStudent: async (code: string, studentId: string, attestation: 'first' | 'second' = 'first') => {
    const { data } = await publicApi.get<StudentDetailData>(
      `/public/report/${code}/student/${studentId}?attestation=${attestation}`
    );
    return data;
  },

  exportPdf: async (code: string) => {
    const response = await publicApi.get(`/public/report/${code}/export/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  exportExcel: async (code: string) => {
    const response = await publicApi.get(`/public/report/${code}/export/excel`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
