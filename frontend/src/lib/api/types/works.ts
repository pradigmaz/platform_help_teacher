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
