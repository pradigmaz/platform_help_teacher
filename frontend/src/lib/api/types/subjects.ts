export type FinalControlType = 'exam' | 'credit' | 'differentiated_credit';

export interface GroupSubjectOffering {
  id: string;
  group_id: string;
  group_name: string;
  subject_id: string;
  subject_name: string;
  semester: string;
  final_control_type: FinalControlType | null;
  exam_question_bank_id?: string | null;
  exam_prep_questions_count: number;
}

export interface AutomaticQueueStudent {
  student_id: string;
  student_name: string;
  completed_count: number;
  automatic_remaining: number;
  completion_at: string | null;
  queue_position: number | null;
  is_winner: boolean;
  is_declined: boolean;
  declined_reason: string | null;
}

export interface AutomaticQueueResponse {
  offering_id: string;
  final_control_type: FinalControlType | null;
  automatic_enabled: boolean;
  automatic_places: number | null;
  total_labs: number;
  students: AutomaticQueueStudent[];
}

export interface OfferingPolicy {
  offering_id: string;
  source: 'explicit' | 'legacy' | string;
  total_labs: number;
  labs_required_first: number;
  labs_required_second_total: number;
  exam_admission_required_labs: number;
  automatic_enabled: boolean;
  automatic_places: number | null;
  automatic_required_labs_total: number;
  second_extra_required: number;
  automatic_extra_required: number;
}

export interface ExamPrepContentValue {
  text?: string;
  content?: Record<string, unknown>;
}

export interface ExamPrepQuestion {
  id: string;
  prompt: string | ExamPrepContentValue;
  answer?: string | ExamPrepContentValue | null;
}
