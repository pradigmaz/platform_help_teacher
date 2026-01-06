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
