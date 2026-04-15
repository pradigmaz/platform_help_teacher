'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TodayLessonAttendance, LessonHistoryItem } from '@/lib/api';
import { Calendar, Users, UserX, Clock, UserCheck, CalendarX, History } from 'lucide-react';

interface TodayLessonsCardProps {
  todayLessons?: TodayLessonAttendance[];
  lessonHistory?: LessonHistoryItem[];
  showNames: boolean;
}

const lessonTypeLabels: Record<string, string> = {
  lecture: 'Лекция',
  practice: 'Практика',
  lab: 'Лабораторная',
};

const lessonTypeColors: Record<string, string> = {
  lecture: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  practice: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  lab: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

export function TodayLessonsCard({ todayLessons, lessonHistory, showNames }: TodayLessonsCardProps) {
  const hasTodayLessons = todayLessons && todayLessons.length > 0;
  const hasHistory = lessonHistory && lessonHistory.length > 0;
  
  if (!hasTodayLessons && !hasHistory) return null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { 
      weekday: 'short', 
      day: 'numeric', 
      month: 'short' 
    });
  };

  const formatFullDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { 
      weekday: 'long', 
      day: 'numeric', 
      month: 'long' 
    });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">
              Сегодня — {formatFullDate(new Date().toISOString())}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {hasTodayLessons ? (
            <div className="space-y-3">
              {todayLessons.map((lesson, idx) => (
                <TodayLessonItem key={idx} lesson={lesson} showNames={showNames} />
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground py-4">
              <CalendarX className="h-5 w-5" />
              <span>Сегодня занятий нет</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* История занятий */}
      {hasHistory && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <History className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-base">История занятий</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {lessonHistory.map((lesson, idx) => (
                <HistoryItem key={idx} lesson={lesson} formatDate={formatDate} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function TodayLessonItem({ lesson, showNames }: { lesson: TodayLessonAttendance; showNames: boolean }) {
  const totalStudents = lesson.present.length + lesson.absent.length + lesson.late.length + lesson.excused.length;
  const attendanceRate = totalStudents > 0 
    ? Math.round(((lesson.present.length + lesson.late.length) / totalStudents) * 100) 
    : 0;

  return (
    <div className="space-y-3 rounded-2xl border border-border/60 p-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="font-medium">{lesson.lesson_number} пара</span>
          <Badge className={lessonTypeColors[lesson.lesson_type] || 'bg-gray-100'}>
            {lessonTypeLabels[lesson.lesson_type] || lesson.lesson_type}
          </Badge>
          {lesson.subgroup && (
            <Badge variant="outline">{lesson.subgroup} п/г</Badge>
          )}
        </div>
        <span className="text-sm text-muted-foreground">
          На занятии: <span className="font-medium">{attendanceRate}%</span>
        </span>
      </div>

      {lesson.topic && (
        <p className="text-sm text-muted-foreground">{lesson.topic}</p>
      )}

      <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <StatItem 
          icon={<UserCheck className="h-3.5 w-3.5 text-green-600" />}
          label="Были"
          count={lesson.present.length}
          names={showNames ? lesson.present : undefined}
        />
        <StatItem 
          icon={<Clock className="h-3.5 w-3.5 text-amber-600" />}
          label="Опоздали"
          count={lesson.late.length}
          names={showNames ? lesson.late : undefined}
        />
        <StatItem 
          icon={<Users className="h-3.5 w-3.5 text-blue-600" />}
          label="Уваж."
          count={lesson.excused.length}
          names={showNames ? lesson.excused : undefined}
        />
        <StatItem 
          icon={<UserX className="h-3.5 w-3.5 text-red-600" />}
          label="Нет"
          count={lesson.absent.length}
          names={showNames ? lesson.absent : undefined}
        />
      </div>
    </div>
  );
}

function HistoryItem({ lesson, formatDate }: { lesson: LessonHistoryItem; formatDate: (d: string) => string }) {
  const rateColor = lesson.attendance_rate >= 80 
    ? 'text-green-600' 
    : lesson.attendance_rate >= 50 
      ? 'text-amber-600' 
      : 'text-red-600';

  return (
    <div className="flex flex-col gap-2 border-b py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <span className="text-sm text-muted-foreground sm:w-20">{formatDate(lesson.date)}</span>
        <Badge variant="outline" className="text-xs">
          {lesson.lesson_number} пара
        </Badge>
        <Badge className={`text-xs ${lessonTypeColors[lesson.lesson_type] || 'bg-gray-100'}`}>
          {lessonTypeLabels[lesson.lesson_type] || lesson.lesson_type}
        </Badge>
        {lesson.subgroup && (
          <span className="text-xs text-muted-foreground">{lesson.subgroup} п/г</span>
        )}
      </div>
      <div className="flex items-center gap-2 text-sm sm:justify-end">
        <span className="text-muted-foreground">{lesson.present_count}/{lesson.total_count}</span>
        <span className={`font-medium ${rateColor}`}>{lesson.attendance_rate}%</span>
      </div>
    </div>
  );
}

function StatItem({ icon, label, count, names }: { 
  icon: React.ReactNode;
  label: string;
  count: number;
  names?: string[];
}) {
  return (
    <div className="space-y-1 rounded-xl border border-border/60 bg-background/70 p-2.5">
      <div className="flex items-center gap-1">
        {icon}
        <span className="text-muted-foreground text-xs">{label}:</span>
        <span className="font-medium text-xs">{count}</span>
      </div>
      {names && names.length > 0 && (
        <ScrollArea className="max-h-16 pl-4">
          <div className="text-xs text-muted-foreground">
            {names.join(', ')}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
