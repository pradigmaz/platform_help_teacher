import type { ExamPrepQuestion } from './subjects';

export interface AdminExamOfferingRef {
  offering_id: string;
  group_id: string;
  group_name: string;
  subject_id: string;
  subject_name: string;
  semester: string;
  questions_count: number;
}

export interface AdminExamQuestionBankSummary {
  bank_id: string;
  subject_id: string;
  subject_name: string;
  semester: string;
  questions_count: number;
  offerings: AdminExamOfferingRef[];
}

export interface AdminExamQuestionBankDetail extends AdminExamQuestionBankSummary {
  questions: ExamPrepQuestion[];
}

export interface AdminExamSubjectGroup {
  subject_id: string;
  subject_name: string;
  semester: string;
  banks: AdminExamQuestionBankSummary[];
  unassigned_offerings: AdminExamOfferingRef[];
}

export interface AdminExamOfferingContext {
  offering: AdminExamOfferingRef;
  bank: AdminExamQuestionBankSummary | null;
  compatible_banks: AdminExamQuestionBankSummary[];
}

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
