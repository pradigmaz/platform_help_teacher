import type { ExamPrepQuestion } from './subjects';

export interface StudentExamPrepOffering {
  offering_id: string;
  subject_id: string;
  subject_name: string;
  semester: string;
  questions_count: number;
}

export interface StudentExamPrepResponse {
  offering_id: string;
  subject_id: string;
  subject_name: string;
  semester: string;
  questions_count: number;
  questions: ExamPrepQuestion[];
}
