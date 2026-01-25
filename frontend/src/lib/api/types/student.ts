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

export interface StudentAttendanceStats {
  total_classes: number;
  present: number;
  late: number;
  excused: number;
  absent: number;
  attendance_rate: number;
}

export interface AttendanceRecord {
  date: string;
  status: 'PRESENT' | 'ABSENT' | 'LATE' | 'EXCUSED';
  lesson_number?: number | null;
  lesson_type?: 'lecture' | 'practice' | 'lab' | null;
}

export interface StudentAttendance {
  stats: StudentAttendanceStats;
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
  deadline_5_lessons?: number | null;
  deadline_4_lessons?: number | null;
  max_grade: number;
  current_max_grade?: number;  // Текущий максимальный балл с учётом дедлайна
  is_available: boolean;
  variant_number?: number;
  submission?: StudentLabSubmission;
  // Поля видимости и дедлайнов по расписанию
  visible_from?: string | null;
  deadline_active_from?: string | null;
  deadline_5_status?: 'active' | 'expired' | null;
  deadline_4_status?: 'active' | 'expired' | null;
  lessons_until_deadline_5?: number | null;
  lessons_until_deadline_4?: number | null;
  // Продление дедлайна
  has_extension?: boolean;
  extension_bonus?: number;
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
  questions?: (string | { text?: string; content?: Record<string, unknown> })[];
  deadline_5_lessons?: number | null;
  deadline_4_lessons?: number | null;
  max_grade: number;
  is_available: boolean;
  variant_number?: number;
  variant_data?: {
    number: number;
    description?: string;
    content?: Record<string, unknown>;
    test_data?: string;
  };
  submission?: StudentLabSubmission;
  // Поля видимости и дедлайнов по расписанию
  visible_from?: string | null;
  deadline_active_from?: string | null;
  deadline_5_status?: 'active' | 'expired' | null;
  deadline_4_status?: 'active' | 'expired' | null;
  lessons_until_deadline_5?: number | null;
  lessons_until_deadline_4?: number | null;
  // Можно ли сейчас сдать (идёт ли пара)
  can_submit_now?: boolean;
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

export interface StudentActivity {
  id: string;
  points: number;
  description: string;
  created_at: string;
}

export interface StudentActivities {
  attestation_type: string;
  stats: {
    total_bonus: number;
    total_penalty: number;
    net_total: number;
    count: number;
  };
  activities: StudentActivity[];
}
