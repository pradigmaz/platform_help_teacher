'use client';

import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Award, TrendingUp, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { LESSON_TYPE_INFO } from '../lib/journal-constants';
import type { Lesson } from '../lib/journal-constants';

interface JournalTableHeaderProps {
  lessons: Lesson[];
  hasAttestationScores: boolean;
  onLessonClick?: (lesson: Lesson) => void;
}

export function JournalTableHeader({
  lessons,
  hasAttestationScores,
  onLessonClick,
}: JournalTableHeaderProps) {
  return (
    <TableHeader className="sticky top-0 z-20 bg-muted/95 backdrop-blur supports-[backdrop-filter]:bg-muted/80">
      <TableRow className="hover:bg-transparent">
        <TableHead className="sticky left-0 z-30 bg-muted/95 backdrop-blur min-w-[220px] font-semibold border-r">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Студент
          </div>
        </TableHead>
        {lessons.map((lesson) => {
          const typeInfo =
            LESSON_TYPE_INFO[lesson.lesson_type as keyof typeof LESSON_TYPE_INFO] || LESSON_TYPE_INFO.LECTURE;
          const Icon = typeInfo.icon;

          return (
            <TableHead
              key={lesson.id}
              className="text-center min-w-[70px] px-2 cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => onLessonClick?.(lesson)}
            >
              <div className="flex flex-col items-center gap-0.5">
                <span className="text-[10px] text-muted-foreground">
                  {format(new Date(lesson.date), 'EEE', { locale: ru })}
                </span>
                <span className="text-xs font-medium">{format(new Date(lesson.date), 'dd.MM')}</span>
                <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${typeInfo.badge}`}>
                  <Icon className="w-3 h-3 mr-0.5" />
                  {typeInfo.shortLabel}
                  {lesson.work_number ? `${lesson.work_number}` : ''}
                  {lesson.subgroup && ` ${lesson.subgroup}п.г.`}
                </Badge>
              </div>
            </TableHead>
          );
        })}
        {hasAttestationScores && (
          <TableHead className="text-center min-w-[80px] font-semibold border-l">
            <div className="flex flex-col items-center">
              <Award className="w-4 h-4" />
              <span className="text-[10px]">ИТОГО</span>
            </div>
          </TableHead>
        )}
        <TableHead className="sticky right-0 z-30 bg-muted/95 backdrop-blur text-center min-w-[60px] font-semibold border-l">
          <div className="flex flex-col items-center">
            <TrendingUp className="w-4 h-4" />
            <span className="text-[10px]">%</span>
          </div>
        </TableHead>
      </TableRow>
    </TableHeader>
  );
}
