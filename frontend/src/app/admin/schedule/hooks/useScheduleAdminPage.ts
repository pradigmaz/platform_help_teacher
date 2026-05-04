'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { addDays, addWeeks, format, getDay, startOfWeek } from 'date-fns';
import api, { ScheduleAPI } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import type { GroupedLecture, LessonSheetData } from '@/components/schedule';
import {
  clearSheetDraft,
  consumeSheetRecoveryPending,
  readSheetDraft,
} from '@/components/schedule/hooks/sheetDraftStorage';
import { getGroupedLectureKey, type RestoredSheetDraft } from '@/components/schedule/hooks/sheetDraftTypes';
import type { LessonData } from '../components';
import type { ScheduleConflict } from '../components/ConflictResolver';
import { mapScheduleLesson } from './scheduleViewModel';

function getInitialWeek(): Date {
  const today = new Date();
  return getDay(today) === 0 ? addWeeks(today, 1) : today;
}

function getInitialRecoveredDraft(): RestoredSheetDraft | null {
  if (!consumeSheetRecoveryPending()) {
    return null;
  }

  const draft = readSheetDraft();
  return draft?.context.route === 'schedule' ? draft : null;
}

export function useScheduleAdminPage() {
  const [lessons, setLessons] = useState<LessonData[]>([]);
  const [groupedLectures, setGroupedLectures] = useState<GroupedLecture[]>([]);
  const [conflicts, setConflicts] = useState<ScheduleConflict[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isParsing, setIsParsing] = useState(false);
  const [currentWeek, setCurrentWeek] = useState(getInitialWeek);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<LessonSheetData | null>(null);
  const [selectedLecture, setSelectedLecture] = useState<GroupedLecture | null>(null);
  const [restoredDraft, setRestoredDraft] = useState<RestoredSheetDraft | null>(getInitialRecoveredDraft);
  const [isParserOpen, setIsParserOpen] = useState(false);
  const [isAutoParserOpen, setIsAutoParserOpen] = useState(false);
  const [isConflictsOpen, setIsConflictsOpen] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastParseRunningRef = useRef(false);
  const recoveryHandledRef = useRef(restoredDraft === null);

  const weekStart = useMemo(() => startOfWeek(currentWeek, { weekStartsOn: 1 }), [currentWeek]);
  const weekEnd = useMemo(() => addDays(weekStart, 5), [weekStart]);
  const weekStartIso = useMemo(() => format(weekStart, 'yyyy-MM-dd'), [weekStart]);
  const weekEndIso = useMemo(() => format(weekEnd, 'yyyy-MM-dd'), [weekEnd]);
  const clearRestoredDraft = useCallback(() => {
    clearSheetDraft();
    setRestoredDraft(null);
    recoveryHandledRef.current = true;
  }, []);

  const loadScheduleView = useCallback(
    async (options?: { silent?: boolean }) => {
      if (!options?.silent) {
        setIsLoading(true);
      }

      try {
        const data = await ScheduleAPI.getAdminView(weekStartIso, weekEndIso);
        const wasRunning = lastParseRunningRef.current;
        const isRunningNow = data.parse_status.is_running;

        setLessons(data.lessons.map(mapScheduleLesson));
        setGroupedLectures(
          data.grouped_lectures.map((lecture) => ({
            date: lecture.date,
            lesson_number: lecture.lesson_number,
            subject_id: lecture.subject_id,
            subject_name: lecture.subject_name,
            topic: lecture.topic,
            room: lecture.room,
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
    void loadScheduleView();
  }, [loadScheduleView]);

  useEffect(() => {
    if (!restoredDraft || recoveryHandledRef.current) {
      return;
    }

    if (restoredDraft.context.weekStartIso !== weekStartIso) {
      setCurrentWeek(new Date(`${restoredDraft.context.weekStartIso}T00:00:00`));
      return;
    }

    if (isLoading) {
      return;
    }

    if (restoredDraft.kind === 'lesson') {
      const lesson = lessons.find((item) => item.id === restoredDraft.lessonId);
      if (lesson) {
        recoveryHandledRef.current = true;
        setSelectedLesson(lesson as LessonSheetData);
        toast.warning('Сессия истекла во время сохранения. Черновик восстановлен, сохраните ещё раз.');
        return;
      }
    } else {
      const lecture = groupedLectures.find(
        (item) => getGroupedLectureKey(item) === restoredDraft.lectureKey
      );
      if (lecture) {
        recoveryHandledRef.current = true;
        setSelectedLecture(lecture);
        toast.warning('Сессия истекла во время сохранения. Черновик восстановлен, сохраните ещё раз.');
        return;
      }
    }

    toast.error('Черновик найден, но нужная карточка в расписании больше не найдена.');
    queueMicrotask(clearRestoredDraft);
  }, [clearRestoredDraft, groupedLectures, isLoading, lessons, restoredDraft, weekStartIso]);

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
    weekStartIso,
    lastUpdated,
    selectedLesson,
    setSelectedLesson,
    selectedLecture,
    setSelectedLecture,
    restoredDraft,
    clearRestoredDraft,
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
