export type SubmissionStatus = 'NEW' | 'READY' | 'IN_REVIEW' | 'REQ_CHANGES' | 'ACCEPTED' | 'REJECTED';

export interface Submission {
  id: string;
  status: SubmissionStatus;
  grade?: number;
  feedback?: string;
  s3_key?: string;
  variant_number?: number;
  ready_at?: string;
  accepted_at?: string;
  created_at: string;
}

export interface LabVariant {
  number: number;
  description: string;
  test_data?: string;
}

export interface Lab {
  id: string;
  number: number;
  title: string;
  topic?: string;
  goal?: string;
  formatting_guide?: string;
  description?: string;
  theory_content?: Record<string, unknown>;
  practice_content?: Record<string, unknown>;
  variants?: LabVariant[];
  questions?: string[];
  deadline?: string;
  max_grade: number;
  is_sequential: boolean;
  is_published?: boolean;
  public_code?: string | null;
  s3_key?: string;
  subject_id?: string;
  lesson_id?: string;
  my_submission?: Submission;
  created_at?: string;
  updated_at?: string;
}

export interface LabCreate {
  number: number;
  title: string;
  topic?: string;
  goal?: string;
  formatting_guide?: string;
  description?: string;
  theory_content?: Record<string, unknown>;
  practice_content?: Record<string, unknown>;
  variants?: LabVariant[];
  questions?: string[];
  deadline?: string;
  max_grade?: number;
  is_sequential?: boolean;
  subject_id?: string;
  lesson_id?: string;
}

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface LabUpdate extends Partial<LabCreate> {}
