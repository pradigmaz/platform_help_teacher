export interface StudentProfile {
  id: string;
  full_name: string;
  username?: string;
  telegram_id?: number;
  vk_id?: number;
  has_telegram?: boolean;
  has_vk?: boolean;
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

export interface StudentDeadlineTrace {
  lesson_index?: number | null;
  current_max_grade: number;
  extension_bonus: number;
  has_extension: boolean;
  is_excused_origin: boolean;
  deadline_5_lessons?: number | null;
  deadline_4_lessons?: number | null;
  effective_deadline_5_lessons?: number | null;
  effective_deadline_4_lessons?: number | null;
  effective_deadline_5_date?: string | null;
  effective_deadline_4_date?: string | null;
  deadline_5_status?: 'active' | 'expired' | null;
  deadline_4_status?: 'active' | 'expired' | null;
  lessons_until_deadline_5?: number | null;
  lessons_until_deadline_4?: number | null;
}

export interface StudentLab {
  id: string;
  number: number;
  title: string;
  subject_id?: string | null;
  topic?: string;
  description?: string;
  deadline_5_lessons?: number | null;
  deadline_4_lessons?: number | null;
  max_grade: number;
  current_max_grade?: number;  // Текущий максимальный балл с учётом дедлайна
  is_available: boolean;
  is_accepted?: boolean;
  journal_grade?: number | null;
  acceptance_source?: 'journal' | 'submission' | null;
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
  deadline_trace?: StudentDeadlineTrace | null;
}

export interface StudentLabDetail {
  id: string;
  number: number;
  title: string;
  subject_id?: string | null;
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
  is_accepted?: boolean;
  journal_grade?: number | null;
  acceptance_source?: 'journal' | 'submission' | null;
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
  has_extension?: boolean;
  extension_bonus?: number;
  is_excused_origin?: boolean;
  deadline_trace?: StudentDeadlineTrace | null;
}

export interface StudentAttestation {
  attestation_type: string;
  subject_id?: string | null;
  total_score: number;
  grade: string;
  is_passing: boolean;
  max_points?: number;
  min_passing_points?: number;
  error?: string;
  lab_progress_plan?: {
    total_required: number;
    first_required: number;
    second_extra_required: number;
    second_total_required: number;
    automatic_extra_required: number;
    automatic_enabled: boolean;
    automatic_places?: number | null;
    completed_count: number;
    automatic_remaining: number;
    automatic_queue_position?: number | null;
    automatic_is_winner?: boolean | null;
    automatic_completion_at?: string | null;
    automatic_reason?: string | null;
    automatic_declined?: boolean;
  } | null;
  breakdown?: {
    labs: { score: number; max: number; count: number; required: number };
    attendance: { score: number; max: number; ratio: number; total_classes: number; present: number; late: number };
    activity: { score: number; max: number; bonus_blocked?: boolean };
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
  subject_id?: string | null;
  stats: {
    total_bonus: number;
    total_penalty: number;
    net_total: number;
    count: number;
  };
  activities: StudentActivity[];
}

export interface StudentAnnouncement {
  id: string;
  title: string;
  content: string;
  is_draft: boolean;
  published_at: string | null;
  created_at: string;
}

export interface StudentDashboardOverview {
  attendance_stats: StudentAttendanceStats;
  labs: StudentLab[];
  attestation_type: 'first' | 'second';
  current_attestation: StudentAttestation | null;
}

export interface StudentDashboardBootstrap {
  profile: StudentProfile;
  semester: {
    semester_start_date: string | null;
    academic_year: number;
    semester: 1 | 2;
  };
  announcements: StudentAnnouncement[];
  overview: StudentDashboardOverview;
}
