'use client';

import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { format, startOfWeek, addDays, getDay, addWeeks } from 'date-fns';
import { Download, Settings, AlertTriangle, Loader2 } from 'lucide-react';
import api, { ScheduleAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/sonner';
import { LessonSheet, LectureSheet, type LessonSheetData, type GroupedLecture } from '@/components/schedule';
import { NotesProvider, useNotesActionsContext } from '@/components/notes';
import { 
  WeekNavigation, 
  ScheduleGrid, 
  ScheduleLegend,
  ParserModal, 
  AutoParserSettings,
  type LessonData
} from './components';
import { ConflictResolver, type ScheduleConflict } from './components/ConflictResolver';

// В воскресенье показываем следующую неделю
function getInitialWeek(): Date {
  const today = new Date();
  return getDay(today) === 0 ? addWeeks(today, 1) : today;
}

// Внутренний компонент с логикой
function SchedulePageContent() {
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
  
  // Modals
  const [isParserOpen, setIsParserOpen] = useState(false);
  const [isAutoParserOpen, setIsAutoParserOpen] = useState(false);
  const [isConflictsOpen, setIsConflictsOpen] = useState(false);
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastParseRunningRef = useRef(false);

  const weekStart = useMemo(
    () => startOfWeek(currentWeek, { weekStartsOn: 1 }),
    [currentWeek],
  );
  // Суббота = Пн + 5 дней
  const weekEnd = useMemo(() => addDays(weekStart, 5), [weekStart]);
  const weekStartIso = useMemo(() => format(weekStart, 'yyyy-MM-dd'), [weekStart]);
  const weekEndIso = useMemo(() => format(weekEnd, 'yyyy-MM-dd'), [weekEnd]);
  const noteLessonIds = useMemo(() => [
    ...lessons.map((lesson) => lesson.id),
    ...groupedLectures.flatMap((lecture) => lecture.groups.map((group) => group.lesson_id)),
  ], [groupedLectures, lessons]);
  const noteLessonIdsKey = noteLessonIds.join('|');

  const loadScheduleView = useCallback(async (options?: { silent?: boolean }) => {
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
        })),
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
        })),
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
  }, [weekEndIso, weekStartIso]);

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

  const handleLessonClick = (lesson: LessonData) => {
    setSelectedLesson(lesson as LessonSheetData);
  };

  const handleLessonAction = async (lessonId: string, action: 'cancel' | 'end_early' | 'restore') => {
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
        action === 'cancel' ? 'Занятие отменено' :
        action === 'end_early' ? 'Отмечено как "отпустил раньше"' :
        'Занятие восстановлено'
      );
      void loadScheduleView();
    } catch {
      toast.error('Ошибка при обновлении занятия');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Расписание</h1>
          <p className="text-muted-foreground mt-1">
            Все занятия за неделю
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {isParsing && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Парсинг...</span>
            </div>
          )}
          {conflicts.length > 0 && (
            <Button variant="outline" onClick={() => setIsConflictsOpen(true)}>
              <AlertTriangle className="w-4 h-4 mr-2 text-yellow-500" />
              Конфликты
              <Badge variant="destructive" className="ml-2">{conflicts.length}</Badge>
            </Button>
          )}
          <Button variant="outline" onClick={() => setIsAutoParserOpen(true)}>
            <Settings className="w-4 h-4 mr-2" />
            Автопарсер
          </Button>
          <Button variant="outline" onClick={() => setIsParserOpen(true)}>
            <Download className="w-4 h-4 mr-2" />
            Парсить
          </Button>
        </div>
      </div>

      {/* Navigation + Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <ScheduleLegend lastUpdated={lastUpdated || undefined} />
        <WeekNavigation 
          currentWeek={currentWeek} 
          onWeekChange={setCurrentWeek} 
        />
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : (
        <ScheduleGrid 
          lessons={lessons}
          groupedLectures={groupedLectures}
          currentWeek={currentWeek}
          onLessonClick={handleLessonClick}
          onLectureClick={setSelectedLecture}
          onLessonAction={handleLessonAction}
        />
      )}

      {/* Modals */}
      <ParserModal 
        open={isParserOpen} 
        onOpenChange={setIsParserOpen}
        onSuccess={() => {
          void loadScheduleView();
        }}
      />
      
      <AutoParserSettings
        open={isAutoParserOpen}
        onOpenChange={setIsAutoParserOpen}
        onParseNow={() => {
          void loadScheduleView();
        }}
        onParsingChange={(nextIsParsing) => {
          setIsParsing(nextIsParsing);
          if (nextIsParsing) {
            lastParseRunningRef.current = true;
          }
        }}
      />
      
      <ConflictResolver
        open={isConflictsOpen}
        onOpenChange={setIsConflictsOpen}
        conflicts={conflicts}
        onRefresh={() => {
          void loadScheduleView();
        }}
      />

      {/* Lesson Sheet */}
      <LessonSheet
        lesson={selectedLesson}
        isOpen={!!selectedLesson}
        onClose={() => setSelectedLesson(null)}
        onSave={() => {
          void loadScheduleView();
          setSelectedLesson(null);
        }}
      />

      {/* Lecture Sheet (grouped) */}
      <LectureSheet
        lecture={selectedLecture}
        isOpen={!!selectedLecture}
        onClose={() => setSelectedLecture(null)}
        onSave={(updatedStatus) => {
          // Optimistic update
          if (selectedLecture && updatedStatus) {
            setGroupedLectures(prev => prev.map(lec => {
              if (lec.date === selectedLecture.date && 
                  lec.lesson_number === selectedLecture.lesson_number &&
                  lec.subject_id === selectedLecture.subject_id) {
                return {
                  ...lec,
                  is_cancelled: updatedStatus === 'cancelled',
                  ended_early: updatedStatus === 'early',
                };
              }
              return lec;
            }));
          }
          setSelectedLecture(null);
        }}
      />
    </div>
  );
}

// Обёртка с NotesProvider для batch-загрузки заметок
export default function SchedulePage() {
  return (
    <NotesProvider>
      <SchedulePageContent />
    </NotesProvider>
  );
}
