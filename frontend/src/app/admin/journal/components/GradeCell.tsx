'use client';

import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import type { GradeData, Lesson } from '../lib/journal-constants';

interface GradeCellProps {
  gradeData: GradeData | undefined;
  lesson: Lesson;
  maxWorkNum: number;
  onGradeChange: (grade: number, workNumber: number | null) => void;
}

export function GradeCell({ gradeData, lesson, maxWorkNum, onGradeChange }: GradeCellProps) {
  const gradeValue = gradeData?.grade;
  const workNum = gradeData?.work_number;
  const lessonWorkNum = lesson.work_number;
  const lessonType = lesson.lesson_type.toLowerCase();
  
  const displayGrade = gradeValue 
    ? (workNum && workNum !== lessonWorkNum ? `${gradeValue}(${workNum})` : `${gradeValue}`)
    : null;
  
  const workNumbers = Array.from({ length: Math.max(maxWorkNum, 8) }, (_, i) => i + 1);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button 
          variant={gradeValue ? 'default' : 'ghost'}
          size="sm" 
          className={`h-5 min-w-5 px-1 text-[10px] rounded ${gradeValue ? 'bg-primary/90' : 'text-muted-foreground/50'}`}
        >
          {displayGrade || '·'}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-3" align="center">
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground mb-2">Оценка:</div>
          <div className="flex gap-1">
            {[2, 3, 4, 5].map(g => (
              <Button
                key={g}
                variant={gradeValue === g ? 'default' : 'outline'}
                size="sm"
                className="h-8 w-8"
                onClick={() => onGradeChange(g, workNum || lessonWorkNum)}
              >
                {g}
              </Button>
            ))}
          </div>
          {(lessonType === 'lab' || lessonType === 'practice') && (
            <>
              <div className="text-xs text-muted-foreground mt-2">
                № работы {lessonWorkNum && <span className="text-primary">(текущая: {lessonWorkNum})</span>}:
              </div>
              <div className="flex gap-1 flex-wrap max-w-[200px]">
                {workNumbers.map(n => (
                  <Button
                    key={n}
                    variant={(workNum || lessonWorkNum) === n ? 'default' : n === lessonWorkNum ? 'secondary' : 'outline'}
                    size="sm"
                    className={`h-6 w-6 text-xs ${n === lessonWorkNum ? 'ring-1 ring-primary' : ''}`}
                    onClick={() => gradeValue && onGradeChange(gradeValue, n)}
                    disabled={!gradeValue}
                  >
                    {n}
                  </Button>
                ))}
              </div>
            </>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
