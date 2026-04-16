'use client';

import { Download, Settings, AlertTriangle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { TooltipProvider } from '@/components/ui/tooltip';
import { LessonSheet, LectureSheet, type LessonSheetData } from '@/components/schedule';
import { getGroupedLectureKey } from '@/components/schedule/hooks/sheetDraftTypes';
import { NotesProvider } from '@/components/notes';
import { 
  WeekNavigation, 
  ScheduleGrid, 
  ScheduleLegend,
  ParserModal, 
  AutoParserSettings
} from './components';
import { ConflictResolver } from './components/ConflictResolver';
import { useScheduleAdminPage } from './hooks/useScheduleAdminPage';

function SchedulePageContent() {
  const {
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
  } = useScheduleAdminPage();

  const restoredLessonDraft =
    restoredDraft?.kind === 'lesson' && restoredDraft.context.route === 'schedule'
      ? restoredDraft
      : null;
  const restoredLectureDraft =
    restoredDraft?.kind === 'lecture' && restoredDraft.context.route === 'schedule'
      ? restoredDraft
      : null;
  const activeLessonDraft =
    restoredLessonDraft && selectedLesson?.id === restoredLessonDraft.lessonId ? restoredLessonDraft : null;
  const activeLectureDraft =
    restoredLectureDraft &&
    selectedLecture &&
    getGroupedLectureKey(selectedLecture) === restoredLectureDraft.lectureKey
      ? restoredLectureDraft
      : null;

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
          onLessonClick={(lesson) => setSelectedLesson(lesson as LessonSheetData)}
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
        onParsingChange={setIsParsing}
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
        onClose={() => {
          if (activeLessonDraft) {
            clearRestoredDraft();
          }
          setSelectedLesson(null);
        }}
        onSave={() => {
          void loadScheduleView();
          clearRestoredDraft();
          setSelectedLesson(null);
        }}
        draftContext={{ route: 'schedule', weekStartIso }}
        restoredDraft={activeLessonDraft}
      />

      {/* Lecture Sheet (grouped) */}
      <LectureSheet
        lecture={selectedLecture}
        isOpen={!!selectedLecture}
        onClose={() => {
          if (activeLectureDraft) {
            clearRestoredDraft();
          }
          setSelectedLecture(null);
        }}
        onSave={() => {
          void loadScheduleView();
          clearRestoredDraft();
          setSelectedLecture(null);
        }}
        draftContext={{ route: 'schedule', weekStartIso }}
        restoredDraft={activeLectureDraft}
      />
    </div>
  );
}

export default function SchedulePage() {
  return (
    <NotesProvider>
      <TooltipProvider delayDuration={150}>
        <SchedulePageContent />
      </TooltipProvider>
    </NotesProvider>
  );
}
