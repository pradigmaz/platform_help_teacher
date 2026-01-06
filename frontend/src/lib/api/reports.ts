import { api, publicApi } from './client';
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

export const ReportsAPI = {
  create: async (payload: ReportCreate) => {
    const { data } = await api.post<Report>('/admin/reports', payload);
    return data;
  },

  list: async () => {
    const { data } = await api.get<ReportListResponse>('/admin/reports');
    return data;
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
  getReport: async (code: string) => {
    const { data } = await publicApi.get<PublicReportData>(`/public/report/${code}`);
    return data;
  },

  verifyPin: async (code: string, pin: string) => {
    const { data } = await publicApi.post<PinVerifyResponse>(
      `/public/report/${code}/verify-pin`,
      { pin }
    );
    return data;
  },

  getStudent: async (code: string, studentId: string) => {
    const { data } = await publicApi.get<StudentDetailData>(
      `/public/report/${code}/student/${studentId}`
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
