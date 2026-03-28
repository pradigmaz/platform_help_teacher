import { api } from './client';
import type { JournalViewResponse } from './types';

export interface JournalViewParams {
  group_id?: string;
  subject_id?: string;
  lesson_type?: string;
  week_start: string;
  week_end: string;
  attestation_period: 'all' | 'first' | 'second';
  academic_year: number;
  semester: 1 | 2;
  semester_start_date?: string | null;
  lesson_id?: string | null;
  include_attestation_scores?: boolean;
}

export const JournalAPI = {
  getView: async (params: JournalViewParams) => {
    const sanitizedParams = Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
    );
    const { data } = await api.get<JournalViewResponse>('/admin/journal/view', { params: sanitizedParams });
    return data;
  },
};
