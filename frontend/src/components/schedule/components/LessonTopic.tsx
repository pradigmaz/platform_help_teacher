'use client';

import { BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { LessonData } from '../types';
import { canHaveGrade } from '../constants';

interface LessonTopicProps {
  lesson: LessonData;
  topic: string;
  workNumber?: number | null;
  availableWorkNumbers: number[];
  onChange: (topic: string) => void;
  onWorkNumberChange?: (workNumber: number | null) => void;
}

export function LessonTopic({
  lesson,
  topic,
  workNumber,
  availableWorkNumbers,
  onChange,
  onWorkNumberChange,
}: LessonTopicProps) {
  const showWorkNumberInput = canHaveGrade(lesson.lesson_type);
  const currentWorkNumber = workNumber === undefined ? lesson.work_number : workNumber;
  const workNumberValue =
    currentWorkNumber !== null &&
    currentWorkNumber !== undefined &&
    availableWorkNumbers.includes(currentWorkNumber)
      ? currentWorkNumber.toString()
      : '';

  return (
    <div className="space-y-3">
      <div className="space-y-1.5">
        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Предмет
        </Label>
        <div className="flex items-center gap-2 text-sm text-muted-foreground px-3 py-2 bg-muted rounded-md">
          <BookOpen className="h-4 w-4" />
          {lesson.subject_name || 'Предмет'}
        </div>
      </div>
      
      {showWorkNumberInput && onWorkNumberChange && (
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Номер работы по умолчанию для пары</Label>
          <div className="flex gap-2">
            <Select
              value={workNumberValue}
              onValueChange={(value) => onWorkNumberChange(parseInt(value, 10))}
            >
              <SelectTrigger className="flex-1" aria-label="Номер лабораторной по умолчанию">
                <SelectValue placeholder="Выберите лабораторную" />
              </SelectTrigger>
              <SelectContent className="z-[10000]">
                {availableWorkNumbers.length > 0 ? (
                  availableWorkNumbers.map((availableWorkNumber) => (
                    <SelectItem
                      key={availableWorkNumber}
                      value={availableWorkNumber.toString()}
                    >
                      ЛР №{availableWorkNumber}
                    </SelectItem>
                  ))
                ) : (
                  <div className="px-2 py-1.5 text-sm text-muted-foreground">
                    По этому предмету ещё нет лабораторных
                  </div>
                )}
              </SelectContent>
            </Select>
            {currentWorkNumber !== null && currentWorkNumber !== undefined ? (
              <Button type="button" variant="outline" onClick={() => onWorkNumberChange(null)}>
                Сбросить
              </Button>
            ) : null}
          </div>
        </div>
      )}
      
      {!showWorkNumberInput && (
        <div className="space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Тема занятия
          </Label>
          <div className="relative">
            <Input
              value={topic}
              onChange={(e) => onChange(e.target.value)}
              placeholder="Введите тему занятия..."
              className={currentWorkNumber ? "pr-16" : ""}
            />
            {currentWorkNumber && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2 bg-muted text-muted-foreground text-[10px] px-1.5 py-0.5 rounded">
                №{currentWorkNumber}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
