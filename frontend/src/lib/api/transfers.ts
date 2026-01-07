import { api } from './client';
import type { TransferRequest, TransferResponse, StudentTransfersResponse } from './types';

export const TransfersAPI = {
  // Перевести студента
  transfer: async (studentId: string, data: TransferRequest): Promise<TransferResponse> => {
    const { data: result } = await api.post<TransferResponse>(
      `/admin/students/${studentId}/transfer`,
      data
    );
    return result;
  },

  // Получить историю переводов студента
  getHistory: async (studentId: string): Promise<StudentTransfersResponse> => {
    const { data } = await api.get<StudentTransfersResponse>(
      `/admin/students/${studentId}/transfers`
    );
    return data;
  },
};
