import { api } from './client';
import { invalidateCached, invalidateCachedByPrefix, loadCached } from './read-cache';
import type {
  StudentProfile,
  StudentAttendance,
  StudentLab,
  StudentLabDetail,
  StudentAttestation,
  StudentTeacherContacts,
  RelinkTelegramResponse,
  StudentActivities,
  AttestationSubjectOption,
  StudentDashboardBootstrap,
} from './types';

const STUDENT_ATTENDANCE_CACHE_KEY = 'student:attendance';
const STUDENT_LABS_CACHE_KEY = 'student:labs';
const STUDENT_LAB_DETAIL_CACHE_PREFIX = 'student:lab-detail:';
const STUDENT_DASHBOARD_BOOTSTRAP_CACHE_KEY = 'student:dashboard-bootstrap';

export const StudentAPI = {
  getProfile: async () => {
    const { data } = await api.get<StudentProfile>('/student/profile');
    return data;
  },

  getDashboardBootstrap: async (options?: { forceRefresh?: boolean }) => {
    return loadCached(
      STUDENT_DASHBOARD_BOOTSTRAP_CACHE_KEY,
      async () => {
        const { data } = await api.get<StudentDashboardBootstrap>('/student/dashboard/bootstrap');
        return data;
      },
      {
        forceRefresh: options?.forceRefresh,
        ttlMs: 30_000,
      },
    );
  },

  getAttendance: async (options?: { forceRefresh?: boolean }) => {
    return loadCached(
      STUDENT_ATTENDANCE_CACHE_KEY,
      async () => {
        const { data } = await api.get<StudentAttendance>('/student/attendance');
        return data;
      },
      {
        forceRefresh: options?.forceRefresh,
      },
    );
  },

  getLabs: async (options?: { forceRefresh?: boolean }) => {
    return loadCached(
      STUDENT_LABS_CACHE_KEY,
      async () => {
        const { data } = await api.get<StudentLab[]>('/student/labs');
        return data;
      },
      {
        forceRefresh: options?.forceRefresh,
      },
    );
  },

  getLabDetail: async (labId: string, options?: { forceRefresh?: boolean }) => {
    return loadCached(
      `${STUDENT_LAB_DETAIL_CACHE_PREFIX}${labId}`,
      async () => {
        const { data } = await api.get<StudentLabDetail>(`/student/labs/${labId}`);
        return data;
      },
      {
        forceRefresh: options?.forceRefresh,
      },
    );
  },

  markLabReady: async (labId: string) => {
    const { data } = await api.post<{ status: string; submission_id: string; variant_number?: number; message: string }>(`/student/labs/${labId}/ready`);
    invalidateCached(STUDENT_LABS_CACHE_KEY);
    invalidateCached(`${STUDENT_LAB_DETAIL_CACHE_PREFIX}${labId}`);
    invalidateCached(STUDENT_DASHBOARD_BOOTSTRAP_CACHE_KEY);
    return data;
  },

  cancelLabReady: async (labId: string) => {
    const { data } = await api.post<{ status: string; message: string }>(`/student/labs/${labId}/cancel-ready`);
    invalidateCached(STUDENT_LABS_CACHE_KEY);
    invalidateCached(`${STUDENT_LAB_DETAIL_CACHE_PREFIX}${labId}`);
    invalidateCached(STUDENT_DASHBOARD_BOOTSTRAP_CACHE_KEY);
    return data;
  },

  getAttestation: async (type: 'first' | 'second', subjectId?: string) => {
    const { data } = await api.get<StudentAttestation>(`/student/attestation/${type}`, {
      params: { subject_id: subjectId },
    });
    return data;
  },

  getAttestationSubjects: async (type: 'first' | 'second') => {
    const { data } = await api.get<AttestationSubjectOption[]>(`/student/attestation/subjects/${type}`);
    return data;
  },

  getTeacherContacts: async (): Promise<StudentTeacherContacts> => {
    const { data } = await api.get<StudentTeacherContacts>('/student/teacher/contacts');
    return data;
  },

  relinkTelegram: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/relink-telegram');
    return data;
  },

  linkVk: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/link-vk');
    return data;
  },

  getActivities: async (attestationType: 'first' | 'second' = 'first', subjectId?: string) => {
    const params = new URLSearchParams({ attestation_type: attestationType });
    if (subjectId) params.append('subject_id', subjectId);
    const { data } = await api.get<StudentActivities>(`/student/activities?${params}`);
    return data;
  },
};

export function resetStudentApiCacheForTests() {
  invalidateCached(STUDENT_ATTENDANCE_CACHE_KEY);
  invalidateCached(STUDENT_LABS_CACHE_KEY);
  invalidateCached(STUDENT_DASHBOARD_BOOTSTRAP_CACHE_KEY);
  invalidateCachedByPrefix(STUDENT_LAB_DETAIL_CACHE_PREFIX);
}
