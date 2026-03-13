import { api } from './client';
import {
  type AttestationType,
  type AttestationSettings,
  type AttestationSettingsUpdate,
  type AttestationResult,
  type AttestationSubjectOption,
  type GroupAttestationResult,
  type GradeScale,
  type BackendGradeScale,
  convertGradeScale,
} from './types';

export const AttestationAPI = {
  getSettings: async (type: AttestationType) => {
    const { data } = await api.get<AttestationSettings>(
      `/admin/attestation/settings/${type}`
    );
    return data;
  },

  updateSettings: async (settings: AttestationSettingsUpdate) => {
    const { data } = await api.put<AttestationSettings>(
      `/admin/attestation/settings`,
      settings
    );
    return data;
  },

  initializeSettings: async () => {
    const { data } = await api.post<{ first: AttestationSettings; second: AttestationSettings }>(
      `/admin/attestation/settings/initialize`
    );
    return data;
  },

  getGradeScale: async (type: AttestationType): Promise<GradeScale> => {
    const { data } = await api.get<BackendGradeScale>(
      `/admin/attestation/grade-scale/${type}`
    );
    return convertGradeScale(data, type);
  },

  calculateStudent: async (
    studentId: string,
    type: AttestationType,
    activityPoints = 0,
    subjectId?: string
  ) => {
    const { data } = await api.get<AttestationResult>(
      `/admin/attestation/calculate/${studentId}/${type}`,
      { params: { activity_points: activityPoints, subject_id: subjectId } }
    );
    return data;
  },

  calculateGroup: async (groupId: string, type: AttestationType, subjectId?: string) => {
    const { data } = await api.get<GroupAttestationResult>(
      `/admin/attestation/calculate/group/${groupId}/${type}`,
      { params: { subject_id: subjectId } }
    );
    return data;
  },

  listGroupSubjects: async (groupId: string, type: AttestationType) => {
    const { data } = await api.get<AttestationSubjectOption[]>(
      `/admin/attestation/subjects/${groupId}/${type}`
    );
    return data;
  },

  calculateAllStudents: async (type: AttestationType, subjectId?: string) => {
    const { data } = await api.get<GroupAttestationResult>(
      `/admin/attestation/scores/all/${type}`,
      { params: { subject_id: subjectId } }
    );
    return data;
  },
};
