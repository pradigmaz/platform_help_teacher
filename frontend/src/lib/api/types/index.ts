import { z } from 'zod';

// --- Zod Schemas ---
export const UserSchema = z.object({
  id: z.string(),
  full_name: z.string(),
  username: z.string().optional(),
  role: z.enum(['student', 'teacher', 'admin']),
});

export type User = z.infer<typeof UserSchema>;

export const AuthResponseSchema = z.object({
  message: z.string(),
  user: UserSchema,
});

export type AuthResponse = z.infer<typeof AuthResponseSchema>;

export function validateResponse<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

// --- Groups ---
export interface StudentImport {
  full_name: string;
  username?: string;
  email?: string;
}

export interface StudentInGroup {
  id: string;
  full_name: string;
  username?: string;
  invite_code?: string;
  subgroup?: number | null;
  is_active: boolean;
}

export interface GroupCreate {
  name: string;
  code: string;
  students: StudentImport[];
}

export interface GroupResponse {
  id: string;
  name: string;
  code: string;
  invite_code?: string;
  students_count: number;
}

export interface GroupDetailResponse {
  id: string;
  name: string;
  code: string;
  invite_code?: string;
  created_at: string;
  students: StudentInGroup[];
}

// --- Labs ---
export type SubmissionStatus = 'NEW' | 'IN_REVIEW' | 'REQ_CHANGES' | 'ACCEPTED' | 'REJECTED';

export interface Submission {
  id: string;
  status: SubmissionStatus;
  grade?: number;
  feedback?: string;
  s3_key?: string;
  created_at: string;
}

export interface Lab {
  id: string;
  title: string;
  description?: string;
  deadline?: string;
  max_grade: number;
  s3_key?: string;
  my_submission?: Submission;
}

// --- Attestation ---
export type AttestationType = 'first' | 'second';

export interface AttestationSettings {
  id: string;
  attestation_type: AttestationType;
  labs_weight: number;
  attendance_weight: number;
  activity_weight: number;
  required_labs_count: number;
  bonus_per_extra_lab: number;
  soft_deadline_penalty: number;
  hard_deadline_penalty: number;
  soft_deadline_days: number;
  present_points: number;
  late_points: number;
  excused_points: number;
  absent_points: number;
  activity_enabled: boolean;
  participation_points: number;
  period_start_date: string | null;
  period_end_date: string | null;
  created_at: string;
  updated_at: string;
  max_points: number;
  min_passing_points: number;
}

export interface AttestationSettingsUpdate {
  attestation_type: AttestationType;
  labs_weight: number;
  attendance_weight: number;
  activity_weight: number;
  required_labs_count: number;
  bonus_per_extra_lab: number;
  soft_deadline_penalty: number;
  hard_deadline_penalty: number;
  soft_deadline_days: number;
  present_points: number;
  late_points: number;
  excused_points: number;
  absent_points: number;
  activity_enabled: boolean;
  participation_points: number;
  period_start_date?: string | null;
  period_end_date?: string | null;
}

export interface ComponentBreakdown {
  labs_raw_score: number;
  labs_weighted_score: number;
  labs_count: number;
  labs_required: number;
  labs_bonus: number;
  attendance_raw_score: number;
  attendance_weighted_score: number;
  attendance_total_classes: number;
  attendance_present: number;
  attendance_late: number;
  attendance_excused: number;
  attendance_absent: number;
  activity_raw_score: number;
  activity_weighted_score: number;
}

export interface AttestationResult {
  student_id: string;
  student_name: string;
  attestation_type: AttestationType;
  total_score: number;
  lab_score: number;
  attendance_score: number;
  activity_score: number;
  grade: string;
  is_passing: boolean;
  max_points: number;
  min_passing_points: number;
  components_breakdown: ComponentBreakdown;
  calculated_at?: string;
  group_code?: string;
}

export interface GroupAttestationResult {
  group_id: string;
  group_code: string;
  attestation_type: AttestationType;
  calculated_at: string;
  total_students: number;
  passing_students: number;
  failing_students: number;
  grade_distribution: Record<string, number>;
  average_score: number;
  students: AttestationResult[];
}

export interface GradeScale {
  max: number;
  min: number;
  grades: {
    excellent: [number, number];
    good: [number, number];
    satisfactory: [number, number];
    unsatisfactory: [number, number];
  };
}

export interface ComponentsConfigAPI {
  labs: {
    enabled: boolean;
    weight: number;
    grading_mode: 'binary' | 'graded';
    grading_scale: 5 | 10 | 100;
    required_count: number;
    bonus_per_extra: number;
    soft_deadline_days: number;
    soft_deadline_penalty: number;
    hard_deadline_penalty: number;
  };
  tests: {
    enabled: boolean;
    weight: number;
    grading_scale: 5 | 10 | 100;
    required_count: number;
    allow_retakes: boolean;
    max_retakes: number;
    retake_penalty: number;
    best_n_count: number | null;
  };
  attendance: {
    enabled: boolean;
    weight: number;
    mode: 'per_class' | 'percentage';
    points_per_class: number;
    max_points: number;
    penalty_enabled: boolean;
    penalty_per_absence: number;
    excused_absence_counts: boolean;
  };
  activity: {
    enabled: boolean;
    weight: number;
    max_points: number;
    points_per_activity: number;
    allow_negative: boolean;
    negative_limit: number;
    categories_enabled: boolean;
  };
}


// --- Works ---
export type WorkType = 'lab' | 'test' | 'independent' | 'colloquium' | 'project';

export interface WorkCreate {
  title: string;
  description?: string;
  max_grade: number;
  deadline?: string;
  order?: number;
}

export interface WorkUpdate {
  title?: string;
  description?: string;
  max_grade?: number;
  deadline?: string;
  order?: number;
  is_active?: boolean;
}

export interface WorkResponse {
  id: string;
  work_type: WorkType;
  title: string;
  description?: string;
  max_grade: number;
  deadline?: string;
  order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkSubmissionCreate {
  work_id: string;
  student_id: string;
  grade?: number;
  feedback?: string;
}

export interface WorkSubmissionUpdate {
  grade?: number;
  feedback?: string;
}

export interface WorkSubmissionResponse {
  id: string;
  work_id: string;
  student_id: string;
  grade?: number;
  feedback?: string;
  submitted_at: string;
  created_at: string;
  updated_at: string;
}

// --- Activities ---
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

// --- Student ---
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

// --- Schedule ---
export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday';
export type LessonType = 'lecture' | 'practice' | 'lab';
export type WeekParity = 'odd' | 'even';

export interface ScheduleItemCreate {
  day_of_week: DayOfWeek;
  lesson_number: number;
  lesson_type: LessonType;
  subject?: string;
  room?: string;
  teacher_id?: string;
  start_date: string;
  end_date?: string;
  week_parity?: WeekParity;
  subgroup?: number;
}

export interface ScheduleItemUpdate {
  day_of_week?: DayOfWeek;
  lesson_number?: number;
  lesson_type?: LessonType;
  subject?: string;
  room?: string;
  teacher_id?: string;
  start_date?: string;
  end_date?: string;
  week_parity?: WeekParity;
  subgroup?: number;
  is_active?: boolean;
}

export interface ScheduleItemResponse {
  id: string;
  group_id: string;
  day_of_week: DayOfWeek;
  lesson_number: number;
  lesson_type: LessonType;
  subject?: string;
  room?: string;
  teacher_id?: string;
  start_date: string;
  end_date?: string;
  week_parity?: WeekParity;
  subgroup?: number;
  is_active: boolean;
}

export interface LessonCreate {
  group_id: string;
  schedule_item_id?: string;
  date: string;
  lesson_number: number;
  lesson_type: LessonType;
  topic?: string;
  work_id?: string;
  subgroup?: number;
}

export interface LessonUpdate {
  topic?: string;
  work_id?: string;
  is_cancelled?: boolean;
  cancellation_reason?: string;
}

export interface LessonResponse {
  id: string;
  group_id: string;
  schedule_item_id?: string;
  date: string;
  lesson_number: number;
  lesson_type: LessonType;
  topic?: string;
  work_id?: string;
  subgroup?: number;
  is_cancelled: boolean;
  cancellation_reason?: string;
}

export interface GenerateLessonsResponse {
  created_count: number;
  lessons: LessonResponse[];
}

export interface ParseScheduleResponse {
  total_parsed: number;
  groups_created: number;
  lessons_created: number;
  lessons_skipped: number;
  subjects_created?: number;
  assignments_created?: number;
  groups: string[];
  subjects?: string[];
  semester_end_detected?: boolean;
  last_lesson_date?: string;
  empty_weeks_count?: number;
}


// --- Reports ---
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

// --- Admin ---
export type ContactVisibility = 'student' | 'report' | 'both' | 'none';

export interface ContactVisibilitySettings {
  telegram: ContactVisibility;
  vk: ContactVisibility;
  max: ContactVisibility;
}

export interface TeacherContactsData {
  contacts: TeacherContacts;
  visibility: ContactVisibilitySettings;
}

export interface TeacherContactsUpdate {
  contacts: TeacherContacts;
  visibility: ContactVisibilitySettings;
}

export interface RelinkTelegramResponse {
  code: string;
  expires_in: number;
}

export interface StudentTeacherContacts {
  contacts: TeacherContacts | null;
  teacher_name?: string;
}
