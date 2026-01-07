export type TransferAttestationType = 'first' | 'second';

export interface AttendanceSnapshot {
  total_lessons: number;
  present: number;
  late: number;
  excused: number;
  absent: number;
}

export interface LabGradeSnapshot {
  work_number: number;
  grade: number;
  lesson_id?: string;
}

export interface TransferRequest {
  to_group_id: string;
  to_subgroup?: number | null;
  transfer_date?: string;
  attestation_type: TransferAttestationType;
}

export interface TransferResponse {
  id: string;
  student_id: string;
  student_name: string;
  from_group_id?: string;
  from_group_name?: string;
  from_subgroup?: number;
  to_group_id?: string;
  to_group_name?: string;
  to_subgroup?: number;
  transfer_date: string;
  attestation_type: TransferAttestationType;
  attendance_data: AttendanceSnapshot;
  lab_grades_data: LabGradeSnapshot[];
  activity_points: number;
  created_at: string;
}

export interface TransferSummary {
  id: string;
  from_group_name?: string;
  from_subgroup?: number;
  to_group_name?: string;
  to_subgroup?: number;
  transfer_date: string;
  attestation_type: TransferAttestationType;
}

export interface StudentTransfersResponse {
  student_id: string;
  student_name: string;
  transfers: TransferSummary[];
}
