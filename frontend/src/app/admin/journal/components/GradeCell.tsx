'use client';

import { useState, useEffect, useRef } from 'react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { GradeData, Lesson } from '../lib/journal-constants';

interface GradeCellProps {
  gradeData: GradeData | undefined;
  lesson: Lesson;
  maxWorkNum: number;
  onGradeChange: (grade: number | null, workNumber: number | null) => void;
}

export function GradeCell({ gradeData, lesson, maxWorkNum, onGradeChange }: GradeCellProps) {
  const gradeValue = gradeData?.grade;
  const workNum = gradeData?.work_number;
  const lessonWorkNum = lesson.work_number;
  const lessonType = lesson.lesson_type.toLowerCase();
  
  const [value, setValue] = useState(gradeValue?.toString() || '');
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync with external changes
  useEffect(() => {
    setValue(gradeValue?.toString() || '');
  }, [gradeValue]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    // Only allow 2-5 or empty
    if (v === '' || /^[2-5]$/.test(v)) {
      setValue(v);
    }
  };

  const handleBlur = () => {
    setIsEditing(false);
    const newGrade = value ? parseInt(value) : null;
    
    if (newGrade === null && gradeValue) {
      // Had value, now empty — delete
      onGradeChange(null, null);
    } else if (newGrade && newGrade !== gradeValue) {
      // New value — save with lesson's work_number
      onGradeChange(newGrade, workNum || lessonWorkNum);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      inputRef.current?.blur();
    } else if (e.key === 'Escape') {
      setValue(gradeValue?.toString() || '');
      setIsEditing(false);
    }
  };

  const handleFocus = () => {
    setIsEditing(true);
    // Select all on focus
    setTimeout(() => inputRef.current?.select(), 0);
  };

  // Show work number indicator if different from lesson's
  const showWorkNum = workNum && workNum !== lessonWorkNum;
  const workNumbers = Array.from({ length: Math.max(maxWorkNum, 8) }, (_, i) => i + 1);

  return (
    <div className="flex items-center gap-0.5">
      <input
        ref={inputRef}
        type="text"
        inputMode="numeric"
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        onFocus={handleFocus}
        onKeyDown={handleKeyDown}
        placeholder="·"
        className={cn(
          "w-5 h-5 text-center text-[10px] rounded border-0 bg-transparent outline-none transition-all",
          "focus:bg-primary focus:text-primary-foreground focus:ring-1 focus:ring-primary",
          value ? "font-semibold text-foreground" : "text-muted-foreground/50",
          isEditing && "bg-primary/10"
        )}
      />
      {/* Work number selector for labs/practices */}
      {(lessonType === 'lab' || lessonType === 'practice') && gradeValue && (
        <Popover>
          <PopoverTrigger asChild>
            <button 
              className={cn(
                "text-[8px] px-0.5 rounded hover:bg-accent",
                showWorkNum ? "text-primary font-medium" : "text-muted-foreground/50"
              )}
            >
              {showWorkNum ? `(${workNum})` : '№'}
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-2" align="center">
            <div className="text-xs text-muted-foreground mb-1">№ работы:</div>
            <div className="flex gap-1 flex-wrap max-w-[160px]">
              {workNumbers.map(n => (
                <Button
                  key={n}
                  variant={(workNum || lessonWorkNum) === n ? 'default' : 'outline'}
                  size="sm"
                  className="h-5 w-5 text-[10px] p-0"
                  onClick={() => onGradeChange(gradeValue, n)}
                >
                  {n}
                </Button>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}
