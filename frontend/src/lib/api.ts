import axios, { AxiosError } from 'axios';
import axiosRetry from 'axios-retry';
import { z } from 'zod';

// --- Custom Error Class ---
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public isRetryable: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// --- Zod Schemas & Types ---

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
  students_count: number;
}

export interface GroupDetailResponse {
  id: string;
  name: string;
  code: string;
  created_at: string;
  students: StudentInGroup[];
}

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
  s3_key?: string; // Ссылка на задание
  my_submission?: Submission;
}

// --- Axios Configuration ---

const baseURL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// Валидация URL для защиты от SSRF (CVE-2025-27152)
function isValidRelativeUrl(url: string | undefined): boolean {
  if (!url) return true;
  // Запрещаем absolute URLs и data: URLs
  if (url.startsWith('http://') || url.startsWith('https://') || 
      url.startsWith('data:') || url.startsWith('//')) {
    return false;
  }
  return true;
}

const api = axios.create({
  baseURL,
  timeout: 30000, // 30 seconds timeout (было 10s)
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Защита от SSRF — блокируем absolute URLs
api.interceptors.request.use((config) => {
  if (!isValidRelativeUrl(config.url)) {
    return Promise.reject(new ApiError(400, 'Invalid URL: absolute URLs are not allowed'));
  }
  return config;
});

axiosRetry(api, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return (
      axiosRetry.isNetworkOrIdempotentRequestError(error) ||
      error.code === 'ERR_NETWORK' ||
      (error.response?.status ? error.response.status >= 500 : false)
    );
  },
});

// --- CSRF Token Management ---
let csrfToken: string | null = null;

async function ensureCsrfToken(): Promise<string> {
  if (!csrfToken) {
    const { data } = await api.get<{ csrf_token: string }>('/auth/csrf-token');
    csrfToken = data.csrf_token;
  }
  return csrfToken;
}

// Reset CSRF token on 403 (token expired/invalid)
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail: string }>) => {
    // Handle offline/network errors
    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Please check your connection.', true));
    }

    if (error.response?.status === 403 && error.response?.data?.detail?.includes('CSRF')) {
      csrfToken = null; // Reset token for retry
      // We could optionally retry the request here if we wanted to auto-refresh CSRF
    }

    const status = error.response?.status || 0;
    const message = error.response?.data?.detail || error.message || 'Something went wrong';
    const isRetryable = status >= 500 || status === 0;
    return Promise.reject(new ApiError(status, message, isRetryable));
  }
);

// --- API Modules ---

export const AuthAPI = {
  login: async (otp: string) => {
    const token = await ensureCsrfToken();
    const { data } = await api.post<AuthResponse>('/auth/otp', { otp }, {
      headers: { 'X-CSRF-Token': token }
    });
    // csrfToken = null; // Reset after use - REMOVED to prevent churn
    return data;
  },
  
  logout: async () => {
    await api.post('/auth/logout');
  },

  me: async () => {
    const { data } = await api.get<User>('/users/me');
    return data;
  }
};

export const GroupsAPI = {
  list: async () => {
    const { data } = await api.get<GroupResponse[]>('/groups/');
    return data;
  },

  get: async (id: string) => {
    const { data } = await api.get<GroupDetailResponse>(`/groups/${id}`);
    return data;
  },

  parseFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<StudentImport[]>('/groups/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  create: async (payload: GroupCreate) => {
    const { data } = await api.post<GroupResponse>('/groups/', payload);
    return data;
  },

  delete: async (id: string) => {
    await api.delete(`/groups/${id}`);
  },

  removeStudent: async (groupId: string, studentId: string) => {
    await api.delete(`/groups/${groupId}/students/${studentId}`);
  },

  addStudent: async (groupId: string, student: { full_name: string; username?: string }) => {
    const { data } = await api.post(`/groups/${groupId}/students`, student);
    return data;
  },

  updateStudent: async (groupId: string, studentId: string, fullName: string) => {
    await api.patch(`/groups/${groupId}/students/${studentId}`, null, {
      params: { full_name: fullName }
    });
  },

  generateCodes: async (groupId: string) => {
    const { data } = await api.post<{ generated: number; total_students: number }>(
      `/groups/${groupId}/generate-codes`
    );
    return data;
  },

  regenerateUserCode: async (userId: string) => {
    const { data } = await api.post<{ invite_code: string }>(
      `/groups/users/${userId}/regenerate-code`
    );
    return data;
  },
};

export const LabsAPI = {
  list: async () => {
    const { data } = await api.get<Lab[]>('/labs/');
    return data;
  },

  uploadSolution: async (labId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await api.post<{ status: string; submission_id: string }>(
      `/labs/${labId}/submit`, 
      formData, 
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return data;
  },
};

// --- Attestation Types ---

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
  group_code?: string; // Для режима "Все студенты"
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

// --- Grade Scale Types ---

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

// --- Components Config Types (for API) ---

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

  exportHyperion: async (groupId: string, type: AttestationType) => {
    const { data } = await api.get(
      `/admin/attestation/export/hyperion/${groupId}/${type}`
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

// --- Works API ---

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

export const WorksAPI = {
  create: async (workType: WorkType, data: WorkCreate) => {
    const { data: response } = await api.post<WorkResponse>(
      '/admin/works',
      { work_type: workType, ...data }
    );
    return response;
  },

  getByType: async (workType: WorkType) => {
    const { data } = await api.get<WorkResponse[]>(`/admin/works/${workType}`);
    return data;
  },

  update: async (workId: string, data: WorkUpdate) => {
    const { data: response } = await api.patch<WorkResponse>(
      `/admin/works/${workId}`,
      data
    );
    return response;
  },

  delete: async (workId: string) => {
    await api.delete(`/admin/works/${workId}`);
  },
};

// --- Work Submissions API ---

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

export const WorkSubmissionsAPI = {
  submit: async (data: WorkSubmissionCreate) => {
    const { data: response } = await api.post<WorkSubmissionResponse>(
      '/admin/work-submissions',
      data
    );
    return response;
  },

  getByStudent: async (studentId: string, workType?: WorkType) => {
    const params = workType ? { work_type: workType } : {};
    const { data } = await api.get<WorkSubmissionResponse[]>(
      `/admin/work-submissions/student/${studentId}`,
      { params }
    );
    return data;
  },

  updateGrade: async (submissionId: string, grade: number, feedback?: string) => {
    const { data } = await api.patch<WorkSubmissionResponse>(
      `/admin/work-submissions/${submissionId}/grade`,
      { grade, feedback }
    );
    return data;
  },

  delete: async (submissionId: string) => {
    await api.delete(`/admin/work-submissions/${submissionId}`);
  },
};

// --- Activities API ---

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

export const ActivitiesAPI = {
  create: async (payload: ActivityCreate) => {
    const { data } = await api.post<ActivityResponse[]>('/admin/activities', payload);
    return data;
  },

  getAll: async (attestationType?: AttestationType, limit = 100) => {
    const params = new URLSearchParams();
    if (attestationType) params.append('attestation_type', attestationType);
    params.append('limit', limit.toString());
    const { data } = await api.get<ActivityWithStudentResponse[]>(`/admin/activities?${params}`);
    return data;
  },

  getByStudent: async (studentId: string) => {
    const { data } = await api.get<ActivityResponse[]>(`/admin/activities/student/${studentId}`);
    return data;
  },

  update: async (id: string, payload: ActivityUpdate) => {
    const { data } = await api.patch<ActivityResponse>(`/admin/activities/${id}`, payload);
    return data;
  },

  delete: async (id: string) => {
    const { data } = await api.delete<ActivityResponse>(`/admin/activities/${id}`);
    return data;
  },
};

// --- Student API (личный кабинет) ---

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

// --- Teacher Contacts for Student ---

export interface StudentTeacherContacts {
  contacts: TeacherContacts | null;
  teacher_name?: string;
}

export const StudentAPI = {
  getProfile: async () => {
    const { data } = await api.get<StudentProfile>('/student/profile');
    return data;
  },

  getAttendance: async () => {
    const { data } = await api.get<StudentAttendance>('/student/attendance');
    return data;
  },

  getLabs: async () => {
    const { data } = await api.get<StudentLab[]>('/student/labs');
    return data;
  },

  getAttestation: async (type: 'first' | 'second') => {
    const { data } = await api.get<StudentAttestation>(`/student/attestation/${type}`);
    return data;
  },

  getTeacherContacts: async (): Promise<StudentTeacherContacts> => {
    const { data } = await api.get<StudentTeacherContacts>('/student/teacher/contacts');
    return data;
  },

  relinkTelegram: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/relink-telegram');
    return data;
  },
};

export default api;


// --- Schedule API ---

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
}

export const ScheduleAPI = {
  getSchedule: async (groupId: string, activeOnly = true) => {
    const { data } = await api.get<ScheduleItemResponse[]>(
      `/admin/groups/${groupId}/schedule`,
      { params: { active_only: activeOnly } }
    );
    return data;
  },

  createScheduleItem: async (groupId: string, item: ScheduleItemCreate) => {
    const { data } = await api.post<ScheduleItemResponse>(
      `/admin/groups/${groupId}/schedule`,
      item
    );
    return data;
  },

  updateScheduleItem: async (itemId: string, item: ScheduleItemUpdate) => {
    const { data } = await api.patch<ScheduleItemResponse>(
      `/admin/schedule/${itemId}`,
      item
    );
    return data;
  },

  deleteScheduleItem: async (itemId: string) => {
    await api.delete(`/admin/schedule/${itemId}`);
  },

  getLessons: async (groupId: string, startDate: string, endDate: string, lessonType?: LessonType) => {
    const params: Record<string, string> = { start_date: startDate, end_date: endDate };
    if (lessonType) params.lesson_type = lessonType;
    const { data } = await api.get<LessonResponse[]>(
      `/admin/groups/${groupId}/lessons`,
      { params }
    );
    return data;
  },

  createLesson: async (lesson: LessonCreate) => {
    const { data } = await api.post<LessonResponse>('/admin/lessons', lesson);
    return data;
  },

  updateLesson: async (lessonId: string, lesson: LessonUpdate) => {
    const { data } = await api.patch<LessonResponse>(`/admin/lessons/${lessonId}`, lesson);
    return data;
  },

  cancelLesson: async (lessonId: string, reason?: string) => {
    const { data } = await api.post<LessonResponse>(
      `/admin/lessons/${lessonId}/cancel`,
      null,
      { params: { reason } }
    );
    return data;
  },

  deleteLesson: async (lessonId: string) => {
    await api.delete(`/admin/lessons/${lessonId}`);
  },

  generateLessons: async (groupId: string, startDate: string, endDate: string) => {
    const { data } = await api.post<GenerateLessonsResponse>(
      `/admin/groups/${groupId}/generate-lessons`,
      { group_id: groupId, start_date: startDate, end_date: endDate }
    );
    return data;
  },

  parseSchedule: async (teacherName: string, startDate: string, endDate: string) => {
    const { data } = await api.post<ParseScheduleResponse>(
      '/admin/schedule/parse',
      { teacher_name: teacherName, start_date: startDate, end_date: endDate }
    );
    return data;
  },
};


// --- Report Types ---

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

// --- Reports API (Admin) ---

export const ReportsAPI = {
  create: async (payload: ReportCreate) => {
    const { data } = await api.post<Report>('/admin/reports', payload);
    return data;
  },

  list: async () => {
    const { data } = await api.get<ReportListResponse>('/admin/reports');
    return data;
  },

  get: async (id: string) => {
    const { data } = await api.get<Report>(`/admin/reports/${id}`);
    return data;
  },

  update: async (id: string, payload: ReportUpdate) => {
    const { data } = await api.put<Report>(`/admin/reports/${id}`, payload);
    return data;
  },

  delete: async (id: string) => {
    await api.delete(`/admin/reports/${id}`);
  },

  regenerate: async (id: string) => {
    const { data } = await api.post<Report>(`/admin/reports/${id}/regenerate`);
    return data;
  },

  getViews: async (id: string) => {
    const { data } = await api.get<ReportViewsResponse>(`/admin/reports/${id}/views`);
    return data;
  },
};

// --- Public Report API (без авторизации) ---

const publicApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Защита от SSRF для публичного API
publicApi.interceptors.request.use((config) => {
  if (!isValidRelativeUrl(config.url)) {
    return Promise.reject(new ApiError(400, 'Invalid URL: absolute URLs are not allowed'));
  }
  return config;
});

publicApi.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: string }>) => {
    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Please check your connection.', true));
    }
    const status = error.response?.status || 0;
    const message = error.response?.data?.detail || error.message || 'Something went wrong';
    const isRetryable = status >= 500 || status === 0;
    return Promise.reject(new ApiError(status, message, isRetryable));
  }
);

// --- Teacher Contacts Types ---

export type ContactVisibility = 'student' | 'report' | 'both' | 'none';

export interface TeacherContacts {
  telegram?: string;
  vk?: string;
  max?: string;
}

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

// --- Admin API (Profile/Settings) ---

export const AdminAPI = {
  getContacts: async (): Promise<TeacherContactsData> => {
    const { data } = await api.get<TeacherContactsData>('/users/profile/contacts');
    return data;
  },

  updateContacts: async (payload: TeacherContactsUpdate): Promise<TeacherContactsData> => {
    const { data } = await api.put<TeacherContactsData>('/users/profile/contacts', payload);
    return data;
  },

  relinkTelegram: async (): Promise<RelinkTelegramResponse> => {
    const { data } = await api.post<RelinkTelegramResponse>('/users/me/relink-telegram');
    return data;
  },
};

// --- Relink Telegram Types ---

export interface RelinkTelegramResponse {
  code: string;
  expires_in: number;
}

export const PublicReportAPI = {
  getReport: async (code: string) => {
    const { data } = await publicApi.get<PublicReportData>(`/public/report/${code}`);
    return data;
  },

  verifyPin: async (code: string, pin: string) => {
    const { data } = await publicApi.post<PinVerifyResponse>(
      `/public/report/${code}/verify-pin`,
      { pin }
    );
    return data;
  },

  getStudent: async (code: string, studentId: string) => {
    const { data } = await publicApi.get<StudentDetailData>(
      `/public/report/${code}/student/${studentId}`
    );
    return data;
  },

  exportPdf: async (code: string) => {
    const response = await publicApi.get(`/public/report/${code}/export/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  exportExcel: async (code: string) => {
    const response = await publicApi.get(`/public/report/${code}/export/excel`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
