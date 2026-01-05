import { BookOpen, FlaskConical, GraduationCap, Check, X, Clock, FileQuestion } from 'lucide-react';

// Types
export interface Group {
  id: string;
  name: string;
  students?: Student[];
}

export interface Student {
  id: string;
  full_name: string;
}

export interface Subject {
  id: string;
  name: string;
}

export interface Lesson {
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
}

export interface GradeData {
  grade: number;
  work_number: number | null;
}

export interface JournalStats {
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

// Constants
export const LESSON_TYPE_INFO: Record<string, { label: string; icon: typeof BookOpen; color: string; short: string }> = {
  LECTURE: { label: 'Лекция', icon: GraduationCap, color: 'bg-blue-500', short: 'Лек' },
  lecture: { label: 'Лекция', icon: GraduationCap, color: 'bg-blue-500', short: 'Лек' },
  LAB: { label: 'Лаб. работа', icon: FlaskConical, color: 'bg-purple-500', short: 'Лаб' },
  lab: { label: 'Лаб. работа', icon: FlaskConical, color: 'bg-purple-500', short: 'Лаб' },
  PRACTICE: { label: 'Практика', icon: BookOpen, color: 'bg-green-500', short: 'Пр' },
  practice: { label: 'Практика', icon: BookOpen, color: 'bg-green-500', short: 'Пр' },
};

export const STATUS_INFO: Record<string, { label: string; icon: typeof Check; color: string }> = {
  PRESENT: { label: 'Присутствует', icon: Check, color: 'text-green-600' },
  LATE: { label: 'Опоздал', icon: Clock, color: 'text-yellow-600' },
  EXCUSED: { label: 'Уваж. причина', icon: FileQuestion, color: 'text-blue-600' },
  ABSENT: { label: 'Отсутствует', icon: X, color: 'text-red-600' },
};

// Helpers
export const canHaveGrade = (lesson: Lesson): boolean => {
  const type = lesson.lesson_type.toLowerCase();
  return type === 'lab' || type === 'practice' || 
         (type === 'lecture' && !!lesson.lecture_work_type);
};
