import type {
  AttendanceStatus,
  GroupedLecture,
  LessonStatus,
  StudentGradeData,
} from '../types';

export interface ScheduleDraftContext {
  route: 'schedule';
  weekStartIso: string;
}

export interface JournalDraftSemester {
  academicYear: number;
  semester: 1 | 2;
}

export interface JournalDraftContext {
  route: 'journal';
  weekStartIso: string;
  groupId: string;
  subjectId: string;
  lessonType: string;
  attestationPeriod: 'all' | 'first' | 'second';
  semester: JournalDraftSemester;
}

export type SheetDraftContext = ScheduleDraftContext | JournalDraftContext;

export interface RestoredLessonDraft {
  kind: 'lesson';
  context: SheetDraftContext;
  lessonId: string;
  topic: string;
  workNumber: number | null;
  status: LessonStatus;
  attendance: Record<string, AttendanceStatus | null>;
  grades: Record<string, StudentGradeData>;
  savedAt: string;
}

export interface RestoredLectureDraft {
  kind: 'lecture';
  context: ScheduleDraftContext;
  lectureKey: string;
  status: LessonStatus;
  attendanceByGroup: Record<string, Record<string, AttendanceStatus | null>>;
  savedAt: string;
}

export type RestoredSheetDraft = RestoredLessonDraft | RestoredLectureDraft;

export function getGroupedLectureKey(
  lecture: Pick<GroupedLecture, 'date' | 'lesson_number' | 'groups'>
): string {
  const lessonIds = lecture.groups.map((group) => group.lesson_id).sort().join(',');
  return `${lecture.date}:${lecture.lesson_number}:${lessonIds}`;
}
