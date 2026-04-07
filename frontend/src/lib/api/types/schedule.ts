export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday';
export type LessonType = 'lecture' | 'practice' | 'lab';
export type WeekParity = 'odd' | 'even';
export type AttendanceSummaryState = 'hidden' | 'not_applicable' | 'unmarked' | 'partial' | 'complete';

export interface LessonAttendanceSummaryResponse {
  state: AttendanceSummaryState;
  marked_count: number;
  expected_count: number;
  is_past: boolean;
}

export interface GroupedLectureAttendanceSummaryResponse {
  state: AttendanceSummaryState;
  marked_count: number;
  expected_count: number;
  is_past: boolean;
}

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
  work_number?: number | null;
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
  work_number?: number | null;
  subgroup?: number;
  is_cancelled: boolean;
  cancellation_reason?: string;
  ended_early: boolean;
  subject_name?: string | null;
  group_name?: string | null;
  summary?: LessonAttendanceSummaryResponse | null;
}

export interface GenerateLessonsResponse {
  created_count: number;
  lessons: LessonResponse[];
}

export interface ScheduleParserConfig {
  enabled: boolean;
  teacher_name: string;
  days_of_week: number[];
  run_time: string;
  parse_days_ahead: number;
}

export interface ScheduleParserConfigResponse extends ScheduleParserConfig {
  id: string;
  teacher_id: string;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ParseScheduleResponse {
  total_parsed: number;
  groups_created: number;
  lessons_created: number;
  lessons_updated: number;
  lessons_skipped: number;
  conflicts_created: number;
  subjects_created: number;
  assignments_created: number;
  groups: string[];
  subjects: string[];
  semester_end_detected: boolean;
  last_lesson_date: string | null;
  empty_weeks_count: number;
}

export type ScheduleAutoParseResponse = ParseScheduleResponse;

export interface ScheduleConflict {
  id: string;
  lesson_id: string;
  conflict_type: 'changed' | 'deleted';
  old_data: {
    topic?: string;
    lesson_type?: string;
    room?: string;
    date?: string;
    lesson_number?: number;
  };
  new_data: {
    topic?: string;
    lesson_type?: string;
    room?: string;
    date?: string;
    lesson_number?: number;
  } | null;
  created_at: string;
}

export interface GroupedLectureGroup {
  id: string;
  name: string;
  lesson_id: string;
}

export interface GroupedLectureResponse {
  date: string;
  lesson_number: number;
  subject_id: string | null;
  subject_name: string | null;
  topic: string | null;
  is_cancelled: boolean;
  ended_early: boolean;
  groups: GroupedLectureGroup[];
  summary?: GroupedLectureAttendanceSummaryResponse | null;
}

export interface ScheduleParseStatusResponse {
  is_running: boolean;
  status?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  lessons_created?: number | null;
  lessons_updated?: number | null;
  lessons_skipped?: number | null;
  conflicts_created?: number | null;
  error_message?: string | null;
  last_run?: string | null;
}

export interface ScheduleViewResponse {
  parse_status: ScheduleParseStatusResponse;
  conflicts: ScheduleConflict[];
  lessons: LessonResponse[];
  grouped_lectures: GroupedLectureResponse[];
  last_updated: string;
}
