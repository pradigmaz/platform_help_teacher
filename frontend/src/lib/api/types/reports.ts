export type ReportType = 'full' | 'attestation_only' | 'attendance_only';

export interface ReportCreate {
  group_id: string;
  report_type?: ReportType;
  expires_in_days?: number | null;
  pin_code?: string | null;
  show_names?: boolean;
  show_grades?: boolean;
  show_attendance?: boolean;
  show_notes?: boolean;
  show_rating?: boolean;
}

export interface ReportUpdate {
  expires_in_days?: number | null;
  pin_code?: string | null;
  remove_pin?: boolean;
  show_names?: boolean;
  show_grades?: boolean;
  show_attendance?: boolean;
  show_notes?: boolean;
  show_rating?: boolean;
  is_active?: boolean;
}

export interface Report {
  id: string;
  code: string;
  group_id: string;
  group_code: string;
  group_name?: string;
  report_type: ReportType;
  expires_at?: string;
  has_pin: boolean;
  show_names: boolean;
  show_grades: boolean;
  show_attendance: boolean;
  show_notes: boolean;
  show_rating: boolean;
  is_active: boolean;
  views_count: number;
  last_viewed_at?: string;
  created_at: string;
  url: string;
}

export interface ReportListResponse {
  reports: Report[];
  total: number;
}

export interface PublicStudentData {
  id: string;
  name?: string;
  total_score?: number;
  lab_score?: number;
  attendance_score?: number;
  activity_score?: number;
  grade?: string;
  is_passing?: boolean;
  attendance_rate?: number;
  present_count?: number;
  absent_count?: number;
  late_count?: number;
  excused_count?: number;
  labs_completed?: number;
  labs_total?: number;
  needs_attention: boolean;
  notes?: string[];
}

export interface AttendanceDistribution {
  present: number;
  late: number;
  excused: number;
  absent: number;
}

export interface LabProgress {
  lab_name: string;
  completed_count: number;
  total_students: number;
  completion_rate: number;
}

export interface TeacherContacts {
  telegram?: string;
  vk?: string;
  max?: string;
}

export interface PublicReportData {
  group_code: string;
  group_name?: string;
  subject_name?: string;
  teacher_name: string;
  report_type: ReportType;
  generated_at: string;
  show_names: boolean;
  show_grades: boolean;
  show_attendance: boolean;
  show_notes: boolean;
  show_rating: boolean;
  total_students: number;
  passing_students?: number;
  failing_students?: number;
  average_score?: number;
  students: PublicStudentData[];
  attendance_distribution?: AttendanceDistribution;
  lab_progress?: LabProgress[];
  grade_distribution?: Record<string, number>;
  teacher_contacts?: TeacherContacts;
}

export interface AttendanceRecordPublic {
  date: string;
  status: string;
  lesson_topic?: string;
}

export interface LabSubmissionPublic {
  lab_id: string;
  lab_name: string;
  lab_number: number;
  grade?: number;
  max_grade: number;
  submitted_at?: string;
  is_submitted: boolean;
  is_late: boolean;
}

export interface ActivityRecordPublic {
  date: string;
  description: string;
  points: number;
}

export interface StudentDetailData {
  id: string;
  name?: string;
  group_code: string;
  total_score?: number;
  lab_score?: number;
  attendance_score?: number;
  activity_score?: number;
  grade?: string;
  is_passing?: boolean;
  max_points: number;
  min_passing_points: number;
  group_average_score?: number;
  rank_in_group?: number;
  total_in_group?: number;
  attendance_rate?: number;
  attendance_history?: AttendanceRecordPublic[];
  present_count?: number;
  absent_count?: number;
  late_count?: number;
  excused_count?: number;
  total_lessons?: number;
  labs_completed?: number;
  labs_total?: number;
  lab_submissions?: LabSubmissionPublic[];
  activity_records?: ActivityRecordPublic[];
  total_activity_points?: number;
  notes?: string[];
  recommendations?: string[];
  needs_attention: boolean;
}

export interface PinVerifyResponse {
  success: boolean;
  message?: string;
  attempts_left?: number;
  retry_after?: number;
}

export interface ReportViewStats {
  total_views: number;
  unique_ips: number;
  last_viewed_at?: string;
  views_by_date: Record<string, number>;
}

export interface ReportViewRecord {
  viewed_at: string;
  ip_address: string;
  user_agent?: string;
}

export interface ReportViewsResponse {
  report_id: string;
  stats: ReportViewStats;
  recent_views: ReportViewRecord[];
}
