import { api } from './client';
import type {
  AttestationType,
  AttestationSettings,
  AttestationSettingsUpdate,
  AttestationResult,
  GroupAttestationResult,
  GradeScale,
  ComponentsConfigAPI,
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

  getGradeScale: async (type: AttestationType) => {
    const { data } = await api.get<GradeScale>(
      `/admin/attestation/grade-scale/${type}`
    );
    return data;
  },

  updateComponentsConfig: async (type: AttestationType, config: ComponentsConfigAPI) => {
    const { data } = await api.patch<AttestationSettings>(
      '/admin/attestation/settings',
      { attestation_type: type, components_config: config }
    );
    return data;
  },

  calculateStudent: async (studentId: string, type: AttestationType, activityPoints = 0) => {
    const { data } = await api.get<AttestationResult>(
      `/admin/attestation/calculate/${studentId}/${type}`,
      { params: { activity_points: activityPoints } }
    );
    return data;
  },

  calculateGroup: async (groupId: string, type: AttestationType) => {
    const { data } = await api.get<GroupAttestationResult>(
      `/admin/attestation/calculate/group/${groupId}/${type}`
    );
    return data;
  },

  calculateAllStudents: async (type: AttestationType) => {
    const { data } = await api.get<GroupAttestationResult>(
      `/admin/attestation/scores/all/${type}`
    );
    return data;
  },
};
