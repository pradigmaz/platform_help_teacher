export interface StudentProfile {
  id: string;
  full_name: string;
  username?: string;
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

export interface StudentLab {
  id: string;
  title: string;
  description?: string;
  deadline?: string;
  max_grade: number;
  submission?: {
    status: string;
    grade?: number;
    feedback?: string;
    submitted_at: string;
  };
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
