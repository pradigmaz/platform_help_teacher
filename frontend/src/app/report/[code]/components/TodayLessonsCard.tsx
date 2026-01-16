'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TodayLessonAttendance } from '@/lib/api';
import { Calendar, Users, UserX, Clock, UserCheck } from 'lucide-react';

interface TodayLessonsCardProps {
  lessons: TodayLessonAttendance[];
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

export function TodayLessonsCard({ lessons, showNames }: TodayLessonsCardProps) {
  if (!lessons || lessons.length === 0) return null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { 
      weekday: 'long', 
      day: 'numeric', 
      month: 'long' 
    });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-base">
            Занятия сегодня — {formatDate(lessons[0].date)}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {lessons.map((lesson, idx) => (
          <LessonItem key={idx} lesson={lesson} showNames={showNames} />
        ))}
      </CardContent>
    </Card>
  );
}

function LessonItem({ lesson, showNames }: { lesson: TodayLessonAttendance; showNames: boolean }) {
  const totalStudents = lesson.present.length + lesson.absent.length + lesson.late.length + lesson.excused.length;
  const attendanceRate = totalStudents > 0 
    ? Math.round(((lesson.present.length + lesson.late.length) / totalStudents) * 100) 
    : 0;

  return (
    <div className="border rounded-lg p-4 space-y-3">
      {/* Header */}
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
        <div className="text-sm text-muted-foreground">
          Посещаемость: <span className="font-medium">{attendanceRate}%</span>
        </div>
      </div>

      {/* Topic */}
      {lesson.topic && (
        <p className="text-sm text-muted-foreground">{lesson.topic}</p>
      )}

      {/* Attendance stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <StatItem 
          icon={<UserCheck className="h-4 w-4 text-green-600" />}
          label="Присутствуют"
          count={lesson.present.length}
          names={showNames ? lesson.present : undefined}
          color="text-green-600"
        />
        <StatItem 
          icon={<Clock className="h-4 w-4 text-amber-600" />}
          label="Опоздали"
          count={lesson.late.length}
          names={showNames ? lesson.late : undefined}
          color="text-amber-600"
        />
        <StatItem 
          icon={<Users className="h-4 w-4 text-blue-600" />}
          label="Уваж. причина"
          count={lesson.excused.length}
          names={showNames ? lesson.excused : undefined}
          color="text-blue-600"
        />
        <StatItem 
          icon={<UserX className="h-4 w-4 text-red-600" />}
          label="Отсутствуют"
          count={lesson.absent.length}
          names={showNames ? lesson.absent : undefined}
          color="text-red-600"
        />
      </div>
    </div>
  );
}

function StatItem({ 
  icon, 
  label, 
  count, 
  names, 
  color 
}: { 
  icon: React.ReactNode;
  label: string;
  count: number;
  names?: string[];
  color: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5">
        {icon}
        <span className="text-muted-foreground">{label}:</span>
        <span className={`font-medium ${color}`}>{count}</span>
      </div>
      {names && names.length > 0 && (
        <div className="text-xs text-muted-foreground pl-5 max-h-20 overflow-y-auto">
          {names.join(', ')}
        </div>
      )}
    </div>
  );
}
