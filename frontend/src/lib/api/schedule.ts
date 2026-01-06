import { api } from './client';
import type {
  LessonType,
  ScheduleItemCreate,
  ScheduleItemUpdate,
  ScheduleItemResponse,
  LessonCreate,
  LessonUpdate,
  LessonResponse,
  GenerateLessonsResponse,
  ParseScheduleResponse,
} from './types';

export const ScheduleAPI = {
  getSchedule: async (groupId: string, activeOnly = true) => {
    const { data } = await api.get<ScheduleItemResponse[]>(
      `/admin/groups/${groupId}/schedule`,
      { params: { active_only: activeOnly } }
    );
    return data;
  },

  createScheduleItem: async (groupId: string, item: ScheduleItemCreate) => {
    const { data } = await api.post<ScheduleItemResponse>(
      `/admin/groups/${groupId}/schedule`,
      item
    );
    return data;
  },

  updateScheduleItem: async (itemId: string, item: ScheduleItemUpdate) => {
    const { data } = await api.patch<ScheduleItemResponse>(
      `/admin/schedule/${itemId}`,
      item
    );
    return data;
  },

  deleteScheduleItem: async (itemId: string) => {
    await api.delete(`/admin/schedule/${itemId}`);
  },

  getLessons: async (groupId: string, startDate: string, endDate: string, lessonType?: LessonType) => {
    const params: Record<string, string> = { start_date: startDate, end_date: endDate };
    if (lessonType) params.lesson_type = lessonType;
    const { data } = await api.get<LessonResponse[]>(
      `/admin/groups/${groupId}/lessons`,
      { params }
    );
    return data;
  },

  createLesson: async (lesson: LessonCreate) => {
    const { data } = await api.post<LessonResponse>('/admin/lessons', lesson);
    return data;
  },

  updateLesson: async (lessonId: string, lesson: LessonUpdate) => {
    const { data } = await api.patch<LessonResponse>(`/admin/lessons/${lessonId}`, lesson);
    return data;
  },

  cancelLesson: async (lessonId: string, reason?: string) => {
    const { data } = await api.post<LessonResponse>(
      `/admin/lessons/${lessonId}/cancel`,
      null,
      { params: { reason } }
    );
    return data;
  },

  deleteLesson: async (lessonId: string) => {
    await api.delete(`/admin/lessons/${lessonId}`);
  },

  generateLessons: async (groupId: string, startDate: string, endDate: string) => {
    const { data } = await api.post<GenerateLessonsResponse>(
      `/admin/groups/${groupId}/generate-lessons`,
      { group_id: groupId, start_date: startDate, end_date: endDate }
    );
    return data;
  },

  parseSchedule: async (teacherName: string, startDate: string, endDate: string) => {
    const { data } = await api.post<ParseScheduleResponse>(
      '/admin/schedule/parse',
      { teacher_name: teacherName, start_date: startDate, end_date: endDate }
    );
    return data;
  },
};
