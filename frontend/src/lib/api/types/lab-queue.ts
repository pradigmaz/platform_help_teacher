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
    test_data?: string;
  };
  questions?: string[];
  ready_at: string;
  status: string;
}

export interface AcceptSubmissionRequest {
  grade: number;
  comment?: string;
}

export interface RejectSubmissionRequest {
  comment: string;
}
