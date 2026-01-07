export interface StudentProfile {
  id: string;
  full_name: string;
  username?: string;
  telegram_id?: number;
  vk_id?: number;
  role: string;
  group?: {
    id: string;
    name: string;
    code: string;
  };
}

export interface AttendanceStats {
  total_classes: number;
  present: number;
  late: number;
  excused: number;
  absent: number;
  attendance_rate: number;
}

export interface AttendanceRecord {
  date: string;
  status: string;
}

export interface StudentAttendance {
  stats: AttendanceStats;
  records: AttendanceRecord[];
}

export interface StudentLabSubmission {
  id: string;
  status: 'NEW' | 'READY' | 'IN_REVIEW' | 'ACCEPTED' | 'REJECTED';
  grade?: number;
  feedback?: string;
  ready_at?: string;
  accepted_at?: string;
}

export interface StudentLab {
  id: string;
  number: number;
  title: string;
  topic?: string;
  description?: string;
  deadline?: string;
  max_grade: number;
  is_available: boolean;
  variant_number?: number;
  submission?: StudentLabSubmission;
}

export interface StudentLabDetail {
  id: string;
  number: number;
  title: string;
  topic?: string;
  goal?: string;
  formatting_guide?: string;
  theory_content?: Record<string, unknown>;
  practice_content?: Record<string, unknown>;
  questions?: string[];
  deadline?: string;
  max_grade: number;
  is_available: boolean;
  variant_number?: number;
  variant_data?: {
    number: number;
    description?: string;
    test_data?: string;
  };
  submission?: StudentLabSubmission;
}

export interface StudentAttestation {
  attestation_type: string;
  total_score: number;
  lab_score?: number;
  attendance_score?: number;
  activity_score?: number;
  grade: string;
  is_passing: boolean;
  max_points?: number;
  min_passing_points?: number;
  error?: string;
  breakdown?: {
    labs: { raw: number; weighted: number; count: number; required: number };
    attendance: { raw: number; weighted: number; total_classes: number; present: number; late: number };
    activity: { raw: number; weighted: number };
  };
}
