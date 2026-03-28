import type { AttestationResult, AttestationSubjectOption } from './attestation';
import type { GroupResponse, StudentInGroup } from './groups';

export interface JournalLessonResponse {
  id: string;
  date: string;
  lesson_number: number;
  lesson_type: string;
  topic: string | null;
  work_number: number | null;
  lecture_work_type: string | null;
  subgroup: number | null;
  is_cancelled: boolean;
  subject_id: string | null;
  subject_name: string | null;
  group_id: string;
  group_name: string | null;
}

export interface JournalStatsResponse {
  total_lessons: number;
  lectures: number;
  labs: number;
  practices: number;
  attendance_rate: number | null;
  average_grade: number | null;
  by_status: {
    present: number;
    late: number;
    excused: number;
    absent: number;
  };
}

export interface JournalResolvedFilters {
  group_id: string | null;
  subject_id: string | null;
  week_start: string;
  week_end: string;
}

export interface JournalGradeCellData {
  grade: number | null;
  work_number: number | null;
  has_conflict?: boolean;
  conflict_count?: number;
}

export interface JournalViewResponse {
  resolved: JournalResolvedFilters;
  groups: GroupResponse[];
  subjects: AttestationSubjectOption[];
  lessons: JournalLessonResponse[];
  students: StudentInGroup[];
  attendance: Record<string, Record<string, string>>;
  grades: Record<string, Record<string, JournalGradeCellData>>;
  attestation_scores: Record<string, AttestationResult>;
  stats: JournalStatsResponse | null;
}
