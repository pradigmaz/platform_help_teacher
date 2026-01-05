'use client';

import { useEffect, useState, useCallback } from 'react';
import { format, startOfWeek, endOfWeek } from 'date-fns';
import { Download, Settings, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/sonner';
import { LessonSheet, type LessonSheetData } from '@/components/schedule';
import { 
  WeekNavigation, 
  ScheduleGrid, 
  ScheduleLegend,
  ParserModal, 
  AutoParserSettings,
  LessonData 
} from './components';
import { ConflictResolver, type ScheduleConflict } from './components/ConflictResolver';

export default function SchedulePage() {
  const [lessons, setLessons] = useState<LessonData[]>([]);
  const [conflicts, setConflicts] = useState<ScheduleConflict[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<LessonSheetData | null>(null);
  
  // Modals
  const [isParserOpen, setIsParserOpen] = useState(false);
  const [isAutoParserOpen, setIsAutoParserOpen] = useState(false);
  const [isConflictsOpen, setIsConflictsOpen] = useState(false);

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });

  useEffect(() => {
    loadConflicts();
  }, []);

  useEffect(() => {
    loadLessons();
  }, [currentWeek]);

  const loadConflicts = async () => {
    try {
      const { data } = await api.get('/admin/schedule/conflicts');
      setConflicts(data);
    } catch {
      // Ignore
    }
  };

  const loadLessons = useCallback(async () => {
    setIsLoading(true);
    
    try {
      const { data } = await api.get('/admin/journal/lessons', {
        params: {
          start_date: format(weekStart, 'yyyy-MM-dd'),
          end_date: format(weekEnd, 'yyyy-MM-dd'),
        },
      });
      setLessons(data);
      setLastUpdated(format(new Date(), 'HH:mm'));
    } catch {
      console.error('Ошибка загрузки занятий');
    } finally {
      setIsLoading(false);
    }
  }, [weekStart, weekEnd]);

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
      loadLessons();
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
        <div className="flex gap-2">
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
          currentWeek={currentWeek}
          onLessonClick={handleLessonClick}
          onLessonAction={handleLessonAction}
        />
      )}

      {/* Modals */}
      <ParserModal 
        open={isParserOpen} 
        onOpenChange={setIsParserOpen}
        onSuccess={loadLessons}
      />
      
      <AutoParserSettings
        open={isAutoParserOpen}
        onOpenChange={setIsAutoParserOpen}
      />
      
      <ConflictResolver
        open={isConflictsOpen}
        onOpenChange={setIsConflictsOpen}
        conflicts={conflicts}
        onRefresh={() => {
          loadConflicts();
          loadLessons();
        }}
      />

      {/* Lesson Sheet */}
      <LessonSheet
        lesson={selectedLesson}
        isOpen={!!selectedLesson}
        onClose={() => setSelectedLesson(null)}
        onSave={() => {
          loadLessons();
          setSelectedLesson(null);
        }}
      />
    </div>
  );
}
