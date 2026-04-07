'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { addDays, addWeeks, format, getDay, startOfWeek } from 'date-fns';
import api, { ScheduleAPI } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import { useNotesActionsContext } from '@/components/notes';
import type { GroupedLecture, LessonSheetData } from '@/components/schedule';
import type { LessonData } from '../components';
import type { ScheduleConflict } from '../components/ConflictResolver';

function getInitialWeek(): Date {
  const today = new Date();
  return getDay(today) === 0 ? addWeeks(today, 1) : today;
}

export function useScheduleAdminPage() {
  const { loadNotesBatch } = useNotesActionsContext();
  const [lessons, setLessons] = useState<LessonData[]>([]);
  const [groupedLectures, setGroupedLectures] = useState<GroupedLecture[]>([]);
  const [conflicts, setConflicts] = useState<ScheduleConflict[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isParsing, setIsParsing] = useState(false);
  const [currentWeek, setCurrentWeek] = useState(getInitialWeek);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<LessonSheetData | null>(null);
  const [selectedLecture, setSelectedLecture] = useState<GroupedLecture | null>(null);
  const [isParserOpen, setIsParserOpen] = useState(false);
  const [isAutoParserOpen, setIsAutoParserOpen] = useState(false);
  const [isConflictsOpen, setIsConflictsOpen] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastParseRunningRef = useRef(false);

  const weekStart = useMemo(() => startOfWeek(currentWeek, { weekStartsOn: 1 }), [currentWeek]);
  const weekEnd = useMemo(() => addDays(weekStart, 5), [weekStart]);
  const weekStartIso = useMemo(() => format(weekStart, 'yyyy-MM-dd'), [weekStart]);
  const weekEndIso = useMemo(() => format(weekEnd, 'yyyy-MM-dd'), [weekEnd]);
  const noteLessonIds = useMemo(
    () => [
      ...lessons.map((lesson) => lesson.id),
      ...groupedLectures.flatMap((lecture) => lecture.groups.map((group) => group.lesson_id)),
    ],
    [groupedLectures, lessons]
  );
  const noteLessonIdsKey = noteLessonIds.join('|');

  const loadScheduleView = useCallback(
    async (options?: { silent?: boolean }) => {
      if (!options?.silent) {
        setIsLoading(true);
      }

      try {
        const data = await ScheduleAPI.getAdminView(weekStartIso, weekEndIso);
        const wasRunning = lastParseRunningRef.current;
        const isRunningNow = data.parse_status.is_running;

        setLessons(
          data.lessons.map((lesson) => ({
            id: lesson.id,
            date: lesson.date,
            lesson_number: lesson.lesson_number,
            lesson_type: lesson.lesson_type,
            topic: lesson.topic ?? null,
            subject_name: lesson.subject_name ?? null,
            work_number: lesson.work_number ?? null,
            subgroup: lesson.subgroup ?? null,
            is_cancelled: lesson.is_cancelled,
            ended_early: lesson.ended_early,
            group_id: lesson.group_id,
            group_name: lesson.group_name ?? null,
            summary: lesson.summary ?? null,
          }))
        );
        setGroupedLectures(
          data.grouped_lectures.map((lecture) => ({
            date: lecture.date,
            lesson_number: lecture.lesson_number,
            subject_id: lecture.subject_id,
            subject_name: lecture.subject_name,
            topic: lecture.topic,
            is_cancelled: lecture.is_cancelled,
            ended_early: lecture.ended_early,
            groups: lecture.groups,
            summary: lecture.summary ?? null,
          }))
        );
        setConflicts(data.conflicts);
        setLastUpdated(format(new Date(data.last_updated), 'HH:mm'));
        setIsParsing(isRunningNow);
        lastParseRunningRef.current = isRunningNow;

        if (wasRunning && !isRunningNow) {
          if (data.parse_status.status === 'success') {
            toast.success(`Автопарсинг завершён: создано ${data.parse_status.lessons_created ?? 0} занятий`);
          } else if (data.parse_status.status === 'failed') {
            toast.error(`Ошибка автопарсинга: ${data.parse_status.error_message || 'Неизвестная ошибка'}`);
          }
        }
      } catch {
        console.error('Ошибка загрузки занятий');
      } finally {
        if (!options?.silent) {
          setIsLoading(false);
        }
      }
    },
    [weekEndIso, weekStartIso]
  );

  useEffect(() => {
    if (noteLessonIds.length === 0) {
      return;
    }
    void loadNotesBatch('lesson', noteLessonIds);
  }, [loadNotesBatch, noteLessonIds, noteLessonIdsKey]);

  useEffect(() => {
    void loadScheduleView();
  }, [loadScheduleView]);

  useEffect(() => {
    if (!isParsing) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }

    pollingRef.current = setInterval(() => {
      void loadScheduleView({ silent: true });
    }, 5000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isParsing, loadScheduleView]);

  const handleLessonAction = useCallback(
    async (lessonId: string, action: 'cancel' | 'end_early' | 'restore') => {
      try {
        const payload = {
          is_cancelled: action === 'cancel',
          ended_early: action === 'end_early',
        };

        if (action === 'restore') {
          payload.is_cancelled = false;
          payload.ended_early = false;
        }

        await api.patch(`/admin/lessons/${lessonId}`, payload);
        toast.success(
          action === 'cancel'
            ? 'Занятие отменено'
            : action === 'end_early'
              ? 'Отмечено как "отпустил раньше"'
              : 'Занятие восстановлено'
        );
        await loadScheduleView();
      } catch {
        toast.error('Ошибка при обновлении занятия');
      }
    },
    [loadScheduleView]
  );

  return {
    lessons,
    groupedLectures,
    conflicts,
    isLoading,
    isParsing,
    setIsParsing,
    currentWeek,
    setCurrentWeek,
    lastUpdated,
    selectedLesson,
    setSelectedLesson,
    selectedLecture,
    setSelectedLecture,
    isParserOpen,
    setIsParserOpen,
    isAutoParserOpen,
    setIsAutoParserOpen,
    isConflictsOpen,
    setIsConflictsOpen,
    loadScheduleView,
    handleLessonAction,
  };
}
