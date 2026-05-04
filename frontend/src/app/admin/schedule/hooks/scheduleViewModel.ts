import type { LessonResponse } from '@/lib/api/types/schedule';
import type { LessonData } from '../components';

export function mapScheduleLesson(lesson: LessonResponse): LessonData {
  return {
    id: lesson.id,
    date: lesson.date,
    lesson_number: lesson.lesson_number,
    lesson_type: lesson.lesson_type,
    topic: lesson.topic ?? null,
    room: lesson.room ?? null,
    subject_id: lesson.subject_id ?? null,
    offering_id: lesson.offering_id ?? null,
    subject_name: lesson.subject_name ?? null,
    work_number: lesson.work_number ?? null,
    subgroup: lesson.subgroup ?? null,
    is_cancelled: lesson.is_cancelled,
    ended_early: lesson.ended_early,
    group_id: lesson.group_id,
    group_name: lesson.group_name ?? null,
    summary: lesson.summary ?? null,
  };
}
