export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday';
export type LessonType = 'lecture' | 'practice' | 'lab';
export type WeekParity = 'odd' | 'even';

export interface ScheduleItemCreate {
  day_of_week: DayOfWeek;
  lesson_number: number;
  lesson_type: LessonType;
  subject?: string;
  room?: string;
  teacher_id?: string;
  start_date: string;
  end_date?: string;
  week_parity?: WeekParity;
  subgroup?: number;
}

export interface ScheduleItemUpdate {
  day_of_week?: DayOfWeek;
  lesson_number?: number;
  lesson_type?: LessonType;
  subject?: string;
  room?: string;
  teacher_id?: string;
  start_date?: string;
  end_date?: string;
  week_parity?: WeekParity;
  subgroup?: number;
  is_active?: boolean;
}

export interface ScheduleItemResponse {
  id: string;
  group_id: string;
  day_of_week: DayOfWeek;
  lesson_number: number;
  lesson_type: LessonType;
  subject?: string;
  room?: string;
  teacher_id?: string;
  start_date: string;
  end_date?: string;
  week_parity?: WeekParity;
  subgroup?: number;
  is_active: boolean;
}

export interface LessonCreate {
  group_id: string;
  schedule_item_id?: string;
  date: string;
  lesson_number: number;
  lesson_type: LessonType;
  topic?: string;
  work_id?: string;
  subgroup?: number;
}

export interface LessonUpdate {
  topic?: string;
  work_id?: string;
  is_cancelled?: boolean;
  cancellation_reason?: string;
}

export interface LessonResponse {
  id: string;
  group_id: string;
  schedule_item_id?: string;
  date: string;
  lesson_number: number;
  lesson_type: LessonType;
  topic?: string;
  work_id?: string;
  subgroup?: number;
  is_cancelled: boolean;
  cancellation_reason?: string;
}

export interface GenerateLessonsResponse {
  created_count: number;
  lessons: LessonResponse[];
}

export interface ParseScheduleResponse {
  total_parsed: number;
  groups_created: number;
  lessons_created: number;
  lessons_skipped: number;
  subjects_created?: number;
  assignments_created?: number;
  groups: string[];
  subjects?: string[];
  semester_end_detected?: boolean;
  last_lesson_date?: string;
  empty_weeks_count?: number;
}
