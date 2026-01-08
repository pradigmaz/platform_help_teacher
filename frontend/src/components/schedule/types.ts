// Types for LessonSheet and related components

export interface Student {
  id: string;
  full_name: string;
  subgroup?: number | null;
}

export interface LessonData {
  id: string;
  date: string;
  lesson_number: number;
  lesson_type: string;
  topic: string | null;
  subject_name: string | null;
  work_number: number | null;
  subgroup: number | null;
  is_cancelled: boolean;
  ended_early?: boolean;
  group_id?: string;
  group_name?: string;
}

export interface GroupWithStudents {
  id: string;
  name: string;
  students: Student[];
}

export type LessonStatus = 'normal' | 'cancelled' | 'early';
export type AttendanceStatus = 'PRESENT' | 'LATE' | 'EXCUSED' | 'ABSENT';

export interface AttendanceRecord {
  student_id: string;
  status: AttendanceStatus;
}

export interface GradeRecord {
  student_id: string;
  grade: number;
  lesson_id: string;
  work_number?: number | null;
}

// Grouped lecture types
export interface LectureGroup {
  id: string;
  name: string;
  lesson_id: string;
}

export interface GroupedLecture {
  date: string;
  lesson_number: number;
  subject_id: string | null;
  subject_name: string | null;
  topic: string | null;
  is_cancelled: boolean;
  ended_early?: boolean;
  groups: LectureGroup[];
}
