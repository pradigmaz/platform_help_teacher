import type { AttestationType } from './attestation';

export interface ActivityCreate {
  student_id?: string;
  group_id?: string;
  points: number;
  description: string;
  attestation_type: AttestationType;
  is_active: boolean;
}

export interface ActivityUpdate {
  points?: number;
  description?: string;
  is_active?: boolean;
}

export interface ActivityResponse {
  id: string;
  student_id: string;
  points: number;
  description: string;
  attestation_type: AttestationType;
  is_active: boolean;
  batch_id?: string;
  created_by_id?: string;
  created_at: string;
}

export interface ActivityWithStudentResponse extends ActivityResponse {
  student_name?: string;
  group_name?: string;
}
