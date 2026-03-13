'use client';
'use no memo';

import { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { GradeData, Lesson } from '../lib/journal-constants';
import { gradeCellSchema, type GradeCellFormValues } from './schema';

interface GradeCellProps {
  gradeData: GradeData | undefined;
  lesson: Lesson;
  maxWorkNum: number;
  onGradeChange: (grade: number | null, workNumber: number | null) => void;
}

export function GradeCell({ gradeData, lesson, maxWorkNum, onGradeChange }: GradeCellProps) {
  const gradeValue = gradeData?.grade;
  const workNum = gradeData?.work_number ?? lesson.work_number ?? null;
  const lessonWorkNum = lesson.work_number;
  const lessonType = lesson.lesson_type.toLowerCase();
  const hasConflict = gradeData?.has_conflict;
  const conflictCount = gradeData?.conflict_count ?? 2;
  
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(gradeValue?.toString() || '');
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const skipBlurSaveRef = useRef(false);

  const form = useForm<GradeCellFormValues>({
    resolver: zodResolver(gradeCellSchema),
    mode: 'onChange',
    defaultValues: {
      grade: gradeValue?.toString() || '',
      work_number: workNum,
    },
  });

  // Sync with external changes
  useEffect(() => {
    const newGrade = gradeValue?.toString() || '';
    setValue(newGrade);
    form.setValue('grade', newGrade, { shouldValidate: false });
    form.setValue('work_number', workNum, { shouldValidate: false });
  }, [gradeValue, workNum, form]);

  // Cleanup debounce on unmount
  useEffect(() => {
    const timer = debounceRef.current;
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    if (v === '' || /^[2-5]$/.test(v)) {
      setValue(v);
      form.setValue('grade', v, { shouldValidate: true });
    }
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (skipBlurSaveRef.current) {
      skipBlurSaveRef.current = false;
      return;
    }
    
    const newGrade = value ? parseInt(value) : null;
    const currentWorkNum = form.getValues('work_number') ?? lessonWorkNum ?? null;
    
    if (newGrade === null && gradeValue) {
      onGradeChange(null, null);
    } else if (newGrade && newGrade !== gradeValue) {
      if ((lessonType === 'lab' || lessonType === 'practice') && !currentWorkNum) {
        setValue(gradeValue?.toString() || '');
        form.setValue('grade', gradeValue?.toString() || '', { shouldValidate: false });
        toast.error('Сначала укажите номер работы');
        return;
      }
      onGradeChange(newGrade, currentWorkNum);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      inputRef.current?.blur();
    } else if (e.key === 'Escape') {
      setValue(gradeValue?.toString() || '');
      form.setValue('grade', gradeValue?.toString() || '');
      setIsEditing(false);
    }
  };

  const handleFocus = () => {
    if (hasConflict) return;
    setIsEditing(true);
    // Select all on focus
    setTimeout(() => inputRef.current?.select(), 0);
  };

  const showWorkNum = workNum && workNum !== lessonWorkNum;
  const needsWorkNum = !workNum && !!value && (lessonType === 'lab' || lessonType === 'practice');
  const workNumbers = Array.from({ length: Math.max(maxWorkNum, 8) }, (_, i) => i + 1);

  if (hasConflict) {
    return (
      <div
        title={`У студента ${conflictCount} оценки на этой паре. Разберите конфликт до редактирования.`}
        className="w-5 h-5 rounded bg-destructive/15 text-destructive text-[10px] font-bold flex items-center justify-center cursor-not-allowed"
      >
        !
      </div>
    );
  }

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
          isEditing && "bg-primary/10",
          needsWorkNum && "ring-1 ring-orange-400"
        )}
      />
      {/* Work number selector for labs/practices */}
      {(lessonType === 'lab' || lessonType === 'practice') && !!value && (
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                skipBlurSaveRef.current = true;
              }}
              className={cn(
                "text-[8px] px-0.5 rounded hover:bg-accent",
                needsWorkNum ? "text-orange-500 font-bold animate-pulse" : 
                showWorkNum ? "text-primary font-medium" : "text-muted-foreground/50"
              )}
            >
              {workNum ? `(${workNum})` : '№?'}
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-2" align="center">
            <div className="text-xs text-muted-foreground mb-1">№ работы:</div>
            <div className="flex gap-1 flex-wrap max-w-[160px]">
              {workNumbers.map(n => (
                <Button
                  key={n}
                  variant={workNum === n ? 'default' : 'outline'}
                  size="sm"
                  className="h-5 w-5 text-[10px] p-0"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    skipBlurSaveRef.current = true;
                  }}
                  onClick={() => {
                    form.setValue('work_number', n);
                    const pendingGrade = value ? parseInt(value, 10) : gradeValue;
                    if (pendingGrade) {
                      onGradeChange(pendingGrade, n);
                    }
                  }}
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
