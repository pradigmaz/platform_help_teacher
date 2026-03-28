export interface QueueItem {
  submission_id: string;
  student_id: string;
  student_name: string;
  group_name: string;
  lab_id: string;
  lab_number: number;
  lab_title: string;
  variant_number?: number;
  ready_at: string;
}

export interface LabQueue {
  lab_id: string;
  lab_number: number;
  lab_title: string;
  queue: QueueItem[];
}

export interface SubmissionDetail {
  submission_id: string;
  student_id: string;
  student_name: string;
  group_id: string;
  group_name: string;
  lab_id: string;
  lab_number: number;
  lab_title: string;
  variant_number?: number;
  variant_data?: {
    number: number;
    description?: string;
    content?: Record<string, unknown>;
    test_data?: string;
  };
  questions?: (string | { text?: string; content?: Record<string, unknown> })[];
  ready_at: string;
  status: string;
  max_allowed_grade: number;  // Максимальная оценка с учётом дедлайна (2-5)
  deadline_trace?: SubmissionDeadlineTrace | null;
}

export interface SubmissionDeadlineTrace {
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

export interface AcceptSubmissionRequest {
  grade: number;
  comment?: string;
}

export interface RejectSubmissionRequest {
  comment: string;
}
